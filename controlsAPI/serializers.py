from rest_framework import serializers
from controlsAPI.models import Control, ControlHierarchy, ControlSet, ControlSetReference
from django.core.validators import RegexValidator, MinValueValidator

class ControlModelSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=None, validators=[RegexValidator(regex='^[a-zA-Z\s]*$', message='Name must only contain alphabetic characters', code='invalid_name')])
    description = serializers.CharField(max_length=None)
    
    class Meta:
        model = Control
        fields = "__all__"

class ControlsetReferenceModelSerializer(serializers.ModelSerializer):
    reference_id = serializers.CharField(max_length=None)
    name = serializers.CharField(max_length=None)  
    
    class Meta:
        model = ControlSetReference
        fields = "__all__"

    #Create a ControlSetReference instance, ensuring the name exists in Control.
    # def create(self, validated_data):
    #     control_instance = self.get_control_instance(validated_data)
    #     validated_data['name'] = control_instance
    #     return ControlSetReference.objects.create(**validated_data)

    # def get_control_instance(self, validated_data):
    #     control_name = validated_data.get('name')
    #     if not control_name:
    #         raise serializers.ValidationError("Name field is required.")

    #     try:
    #         return Control.objects.get(name=control_name)
    #     except Control.DoesNotExist:
    #         raise serializers.ValidationError(f"Control with name '{control_name}' does not exist.")

class ControlsetModelSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(max_length= None,read_only=True)
    name = serializers.CharField(max_length=None, validators=[RegexValidator(regex='^[a-zA-Z\s]*$', message='Name must only contain alphabetic characters', code='invalid_name')],)
    hierarchy_depth = serializers.IntegerField(validators=[MinValueValidator(0)])
    
    class Meta:
        model = ControlSet
        fields = "__all__"

class ListField(serializers.ListField):
    child = serializers.CharField()

class ControlHierarchyModelSerializer(serializers.ModelSerializer):
    control_set = ControlsetReferenceModelSerializer(many=True, required=False)
    parents = ListField(default=[], allow_empty=True)
    children = ListField(default=[], allow_empty=True)

    class Meta:
        model = ControlHierarchy
        fields = "__all__"
    
    # Custom validation for parents and children using hierarchy depth.
    def validate(self, attrs):
        parent_value = attrs.get('parents', [])
        children_value = attrs.get('children', [])
        existing_controlset_names = set(ControlSet.objects.values_list('name', flat=True))
        slug = self.instance.slug if self.instance else None
        if slug:
            try:
                control_set_instance = ControlSet.objects.get(slug=slug)
                hierarchical_depth = control_set_instance.hierarchy_depth
            except ControlSet.DoesNotExist:
                hierarchical_depth = None

        if hierarchical_depth == 0 and len(parent_value)>0:
            raise serializers.ValidationError("Parents do not exist")

        for parent_name in parent_value:
            if parent_name not in existing_controlset_names:
                raise serializers.ValidationError(f"Parent ControlSet '{parent_name}' does not exist.")
            parent_instance = ControlSet.objects.get(name=parent_name)
            if parent_instance.hierarchy_depth >= hierarchical_depth:
                raise serializers.ValidationError(f"Parent ControlSet '{parent_name}' has greater hierarchy depth than the current ControlSet(It can't be a parent).")

        for child_name in children_value:
            if child_name not in existing_controlset_names:
                raise serializers.ValidationError(f"Child ControlSet '{child_name}' does not exist.")
            child_instance = ControlSet.objects.get(name=child_name)
            if child_instance.hierarchy_depth <= hierarchical_depth:
                raise serializers.ValidationError(f"Child ControlSet '{child_name}' has lesser hierarchy depth than the current ControlSet(It can't be a child).")

        return attrs
    
    # Update the control_set in ControlHierarchy instance with validated data.
    def update(self, instance, validated_data):
        control_set_data = validated_data.pop('control_set', None)
        if control_set_data:
            control_set_instances = []
            for data in control_set_data:
                reference_id = data.get('reference_id')
                try:
                    control_set_instance = ControlSetReference.objects.get(reference_id=reference_id)
                    control_set_instances.append(control_set_instance)
                except ControlSetReference.DoesNotExist:
                    raise serializers.ValidationError(f"ControlSetReference {reference_id} does not exist")
            instance.control_set.add(*control_set_instances)
            
        parents = validated_data.get('parents', [])
        instance.parents = parents  

        children = validated_data.get('children', [])
        instance.children = children  
        
        instance.save()

        for parent_name in parents:
            try:
                parent_control_set = ControlSet.objects.get(name=parent_name)
                control_set_slug = parent_control_set.slug
                parent_instance = ControlHierarchy.objects.get(slug=control_set_slug)
            except ControlSet.DoesNotExist:
                raise serializers.ValidationError(f"Parent ControlSet '{parent_name}' does not exist.")
            except ControlHierarchy.DoesNotExist:
                raise serializers.ValidationError(f"No ControlHierarchy found with slug {control_set_slug}")
            parent_instance.control_set.add(*control_set_instances)
            parent_instance.save()
        return instance
        



        

