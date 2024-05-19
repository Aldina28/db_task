from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .serializers import ControlHierarchyModelSerializer, ControlModelSerializer, ControlsetModelSerializer, ControlsetReferenceModelSerializer
from .models import ControlHierarchy, ControlSet, Control, ControlSetReference
from django.db import DatabaseError, transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class ControlCreateAPI(APIView):
    @swagger_auto_schema(
        request_body=ControlModelSerializer,
        responses={201: ControlModelSerializer(many=False)}
    )
    def post(self, request):
        control_serializer = ControlModelSerializer(data=request.data)
        try:
            if control_serializer.is_valid():
                control_serializer.save()
                return Response(control_serializer.data, status=status.HTTP_201_CREATED)
            return Response(control_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except DatabaseError as e:
            error_message = "Failed to create Control, Control name already exist"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        
class ControlDeleteAPI(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the Control to delete')
            },
            required=['name']
        ),
        responses={
            200: "ControlSet, ControlSetReferences, and ControlHierarchy components deleted successfully",
            404: "No Control found with the specified name",
            400: "Invalid request data"
        }
    )
    def delete(self, request):
        name = request.data.get("name")
        try:
            control_obj = Control.objects.get(name=name)
            control_set_ref_objs = ControlSetReference.objects.filter(name=control_obj.name)
            control_set_ref_objs.delete()
            control_hierarchies = ControlHierarchy.objects.filter(control_set__name=name)
            for hierarchy in control_hierarchies:
                hierarchy.control_set.remove(control_obj)
            control_obj.delete()
            control_hierarchies.delete()
            return Response({"msg": "Control, ControlSetReferences, and ControlHierarchy components deleted successfully"})
        except Control.DoesNotExist:
            return Response({"msg": f"No Control found with name {name}"}, status=status.HTTP_404_NOT_FOUND)

class AllControlDetailsAPI(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'name',
                openapi.IN_QUERY,
                description="Name of the Control to retrieve",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: openapi.Response('Successful retrieval of Control data', ControlModelSerializer(many=True)),
            404: openapi.Response('No object found with the specified name', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'msg': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )),
            400: openapi.Response('Invalid request data', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'msg': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ))
        }
    )
    def get(self, request):
        name = request.query_params.get("name")
        # name = request.data.get("name")
        if name:
            try:
                control_obj = Control.objects.get(name=name)
                control_serializer = ControlModelSerializer(control_obj)
                return Response(control_serializer.data, status=status.HTTP_200_OK)
            except Control.DoesNotExist:
                return Response({"msg": f"No object found with name {name}"}, status=status.HTTP_404_NOT_FOUND)
        else:
            controls = Control.objects.all()
            control_serializer = ControlModelSerializer(controls, many=True)
            return Response(control_serializer.data, status=status.HTTP_200_OK)

class ControlUpdateAPI(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the Control to delete'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description to be updated')
            },
            required=['name']
        ),
        responses={
            200: openapi.Response(description="Control and associated ControlSetReferences updated successfully"),
            404: "No Control found with the specified name",
            400: "Invalid request data"
        }
    )
    def put(self, request):
        name = request.data.get("name")
        try:
            Control_obj = Control.objects.get(name=name)
        except Control.DoesNotExist:
            return Response({"msg": f"No Control found with name {name}"}, status=status.HTTP_404_NOT_FOUND)
        control_serializer = ControlModelSerializer(Control_obj, data=request.data, partial=True)
        if control_serializer.is_valid():
            control_serializer.save()
            if name:
                control_set_references = ControlSetReference.objects.filter(name=name)
                for ref in control_set_references:
                    ref.name = name
                    ref.save()
            return Response({
                "control": control_serializer.data,
                "msg": "Associated ControlSetReferences updated successfully"
            }, status=status.HTTP_200_OK)
        return Response(control_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ControlsetRefUpdateAPI(APIView):
        @swagger_auto_schema(
            request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the Control to delete'),
                    'reference_id': openapi.Schema(type=openapi.TYPE_STRING, description='Reference id to be updated')
                },
                required=['name', 'reference_id']
            ),
            responses={
                200: openapi.Response(description="Control and associated ControlSetReferences updated successfully"),
                404: "No Control found with the specified name",
                400: "Invalid request data"
            }
        )
        def put(self, request):
            name = request.data.get("name")
            new_reference_id = request.data.get("reference_id")
            if not name or not new_reference_id:
                return Response({"msg": "Name and new reference_id are required"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                control_set_ref = ControlSetReference.objects.get(name=name)
            except ControlSetReference.DoesNotExist:
                return Response({"msg": f"No ControlSetReference found with name {name}"}, status=status.HTTP_404_NOT_FOUND)
            if 'name' in request.data and request.data['name'] != control_set_ref.name:
                return Response({"msg": "The name field cannot be updated here. Name can only be updated in Control."}, status=status.HTTP_400_BAD_REQUEST)
            serializer = ControlsetReferenceModelSerializer(control_set_ref, data=request.data, partial=True)
            if serializer.is_valid():
                old_reference_id = control_set_ref.reference_id
                with transaction.atomic():
                    serializer.save()
                    control_hierarchies = ControlHierarchy.objects.filter(control_set=control_set_ref)
                    for hierarchy in control_hierarchies:
                        control_set = hierarchy.control_set.all()
                        for cs_ref in control_set:
                            if cs_ref.reference_id == old_reference_id:
                                cs_ref.reference_id = new_reference_id
                                cs_ref.save()
                    return Response({"msg": "ControlSetReference and ControlHierarchy components updated successfully"}, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AllControlsetRefDetailsAPI(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'name',
                openapi.IN_QUERY,
                description="Name of the object to retrieve",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: openapi.Response('Successful retrieval of data', ControlsetReferenceModelSerializer(many=True)),
            404: openapi.Response('No object found with the specified name', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'msg': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )),
            400: openapi.Response('Invalid request data', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'msg': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ))
        }
    )
    def get(self, request):
        name = request.query_params.get("name")
        # name = request.data.get("name")
        if name:
            try:
                Control_set_ref_obj = ControlSetReference.objects.get(name=name)
                controlsetref_serializer = ControlsetReferenceModelSerializer(Control_set_ref_obj)
                return Response(controlsetref_serializer.data)
            except ControlSetReference.DoesNotExist:
                return Response({"msg": f"No object found with name {name}"}, status=status.HTTP_404_NOT_FOUND)
        else:
            controlsetref = ControlSetReference.objects.all()
            controlsetref_serializer = ControlsetReferenceModelSerializer(controlsetref, many=True)
            return Response(controlsetref_serializer.data)

class ControlSetCreateAPI(APIView):
    @swagger_auto_schema(
        request_body=ControlsetModelSerializer,
        responses={201: ControlsetModelSerializer(many=False)}
    )
    def post(self, request):
        controlset_serializer = ControlsetModelSerializer(data=request.data)
        try:
            if controlset_serializer.is_valid():
                controlset_serializer.save()
                return Response(controlset_serializer.data, status=status.HTTP_201_CREATED)
            return Response(controlset_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except DatabaseError as e:
            error_message = "Failed to create ControlSet"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)

class ControlSetUpdateAPI(APIView):
    @swagger_auto_schema(
            request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the Control set to delete'),
                    'hierarchy_depth': openapi.Schema(type=openapi.TYPE_STRING, description='Hierarchy depth to be updated')
                },
                required=['name']
            ),
            responses={
                200: openapi.Response(description="Control set updated successfully"),
                404: "No Control set found with the specified name",
                400: "Invalid request data"
            }
        )
    def put(self, request):
        name = request.data.get("name")
        try:
            ControlSet_obj = ControlSet.objects.get(name=name)
        except ControlSet.DoesNotExist:
            return Response({"msg": f"No ControlSet found with name {name}"}, status=status.HTTP_404_NOT_FOUND)
        controlset_serializer = ControlsetModelSerializer(ControlSet_obj, data=request.data, partial=True)
        if controlset_serializer.is_valid():
            controlset_serializer.save()
            return Response(controlset_serializer.data)
        return Response(controlset_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ControlSetDeleteAPI(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the Control set to delete')
            },
            required=['name']
        ),
        responses={
            200: "ControlSet and ControlHierarchy components deleted successfully",
            404: "No Control set found with the specified name",
            400: "Invalid request data"
        }
    )
    def delete(self, request):
        name = request.data.get("name")
        try:
                control_set_obj = ControlSet.objects.get(name=name)
                control_hierarchy_objs = ControlHierarchy.objects.all()
                for control_hierarchy_obj in control_hierarchy_objs:
                    if control_set_obj.name in control_hierarchy_obj.parents:
                        control_hierarchy_obj.parents.remove(control_set_obj.name)
                    if control_set_obj.name in control_hierarchy_obj.children:
                        control_hierarchy_obj.children.remove(control_set_obj.name)
                    control_hierarchy_obj.save()
                control_set_obj.delete()
                return Response({"msg": "ControlSet, ControlHierarchies deleted successfully"})
        except ControlSet.DoesNotExist:
            return Response({"msg": f"No ControlSet found with name {name}"}, status=status.HTTP_404_NOT_FOUND)

class AllControlSetDetailsAPI(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'name',
                openapi.IN_QUERY,
                description="Name of the object to retrieve",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: openapi.Response('Successful retrieval of data', ControlHierarchyModelSerializer(many=True)),
            404: openapi.Response('No object found with the specified name', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'msg': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )),
            400: openapi.Response('Invalid request data', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'msg': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ))
        }
    )
    def get(self, request):
        name = request.query_params.get("name")
        # name = request.data.get("name")
        if name:
            try:
                ControlSet_obj = ControlSet.objects.get(name=name)
                controlset_serializer = ControlsetModelSerializer(ControlSet_obj)
                return Response(controlset_serializer.data)
            except ControlSet.DoesNotExist:
                return Response({"msg": f"No object found with name {name}"}, status=status.HTTP_404_NOT_FOUND)
        else:
            controlset = ControlSet.objects.all()
            controlset_serializer = ControlsetModelSerializer(controlset, many=True)
            return Response(controlset_serializer.data)

class ControlHierarchyUpdateAPI(APIView):
    @swagger_auto_schema(
            request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the Control set to delete'),
                    'control_set': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description='List of control set'),
                    'parents': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description='List of parent names'),
                    'children': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description='List of child names')
                },
                required=['name']
            ),
            responses={
                200: openapi.Response(description="Control set updated successfully"),
                404: "No Control set found with the specified name",
                400: "Invalid request data"
            }
        )
    def put(self, request):
        name = request.data.get("name")
        if not name:
            return Response({"msg": "Name is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            create_set_obj = ControlSet.objects.get(name=name)
            slug = create_set_obj.slug
        except ControlSet.DoesNotExist:
            return Response({"msg": f"No CreateSet found with name {name}"}, status=status.HTTP_404_NOT_FOUND)
        try:
            controlhierarchy_obj = ControlHierarchy.objects.get(slug=slug)
        except ControlHierarchy.DoesNotExist:
            return Response({"msg": f"No ControlHierarchy found with slug {slug}"}, status=status.HTTP_404_NOT_FOUND)
        try:
            controlhierarchy_serializer = ControlHierarchyModelSerializer(controlhierarchy_obj, data=request.data, partial=True)
            controlhierarchy_serializer.is_valid(raise_exception=True)
            controlhierarchy_serializer.save()
            return Response(controlhierarchy_serializer.data)
        except DatabaseError as e:
            error_message = "Don't update the already existing data. Enter only the new data"
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
        
class AllControlHierarchiesDetailsAPI(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'name',
                openapi.IN_QUERY,
                description="Name of the object to retrieve",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: openapi.Response('Successful retrieval of data', ControlHierarchyModelSerializer(many=True)),
            404: openapi.Response('No object found with the specified name', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'msg': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )),
            400: openapi.Response('Invalid request data', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'msg': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ))
        }
    )
    def get(self, request):
        name = request.query_params.get("name")
        # name = request.data.get("name")
        def add_control_details(control_set_data):
            for control_set_item in control_set_data:
                reference_id = control_set_item.get('reference_id')
                try:
                    control_set_ref = ControlSetReference.objects.get(reference_id=reference_id)
                    control_set_item['control_name'] = control_set_ref.name
                    try:
                        control = Control.objects.get(name=control_set_ref.name)
                        control_set_item['description'] = control.description
                    except Control.DoesNotExist:
                        control_set_item['description'] = "Description not found"
                except ControlSetReference.DoesNotExist:
                    control_set_item['control_name'] = "Reference not found"
                    control_set_item['description'] = "Description not found"
        if name:
            try:
                create_set_obj = ControlSet.objects.get(name=name)
                slug = create_set_obj.slug
            except ControlSet.DoesNotExist:
                return Response({"msg": f"No Control Set found with name {name}"}, status=status.HTTP_404_NOT_FOUND)
            try:
                controlhierarchy_obj = ControlHierarchy.objects.get(slug=slug)
                controlhierarchy_serializer = ControlHierarchyModelSerializer(controlhierarchy_obj)
                control_set_data = controlhierarchy_serializer.data.get('control_set', [])
                add_control_details(control_set_data)
                response_data = controlhierarchy_serializer.data
                response_data['control_set_name'] = create_set_obj.name  
                return Response(response_data)
            except ControlHierarchy.DoesNotExist:
                return Response({"msg": f"No ControlHierarchy found with slug {slug}"}, status=status.HTTP_404_NOT_FOUND)
        else:
            controlhierarchy = ControlHierarchy.objects.all()
            controlhierarchy_serializer = ControlHierarchyModelSerializer(controlhierarchy, many=True)
            for control_hierarchy_data in controlhierarchy_serializer.data:
                control_set_data = control_hierarchy_data.get('control_set', [])
                add_control_details(control_set_data)
                slug = control_hierarchy_data.get('slug')
                try:
                    create_set_obj = ControlSet.objects.get(slug=slug)
                    control_hierarchy_data['control_set_name'] = create_set_obj.name  
                except ControlSet.DoesNotExist:
                    control_hierarchy_data['control_set_name'] = "Name not found"
            return Response(controlhierarchy_serializer.data)

        
class ControlHierarchyControlsetDeleteAPI(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Object to delete'),
                'reference_id': openapi.Schema(type=openapi.TYPE_STRING, description='Reference id to delete')
            },
            required=['name']
        ),
        responses={
            200: "ControlSet and ControlHierarchy components deleted successfully",
            404: "No Control set found with the specified name",
            400: "Invalid request data"
        }
    )
    def delete(self, request):
        name = request.data.get("name")
        reference_id = request.data.get("reference_id")
        if not name or not reference_id:
            return Response({"msg": "Both 'name' and 'reference_id' are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            control_set = ControlSet.objects.get(name=name)
            slug = control_set.slug
        except ControlSet.DoesNotExist:
            return Response({"msg": f"No Control Set found with name {name}"}, status=status.HTTP_404_NOT_FOUND)
        try:
            control_hierarchy = ControlHierarchy.objects.get(slug=slug)
        except ControlHierarchy.DoesNotExist:
            return Response({"msg": f"No ControlHierarchy found with slug {slug}"}, status=status.HTTP_404_NOT_FOUND)
        try:
            control_set_ref = ControlSetReference.objects.get(reference_id=reference_id)
        except ControlSetReference.DoesNotExist:
            return Response({"msg": f"No ControlSetReference found with reference_id {reference_id}"}, status=status.HTTP_404_NOT_FOUND)
        control_hierarchy.control_set.remove(control_set_ref)
        parents = control_hierarchy.parents
        for parent_name in parents:
            try:
                parent_control_set = ControlSet.objects.get(name=parent_name)
                parent_slug = parent_control_set.slug
                parent_hierarchy = ControlHierarchy.objects.get(slug=parent_slug)
                parent_hierarchy.control_set.remove(control_set_ref)
            except ControlSet.DoesNotExist:
                continue  
            except ControlHierarchy.DoesNotExist:
                continue 
        return Response({"msg": "ControlSetReference deleted successfully from ControlHierarchy and its parents"}, status=status.HTTP_200_OK)
    