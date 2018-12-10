from api.serializers import shift_serializer, employee_serializer
from rest_framework import serializers
from django.db.models import Q
from api.models import Clockin
from api.utils.utils import haversine

class ClockinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clockin
        exclude = ()
        
    def validate(self, data):
        
        if 'started_at' in data:
            
            if 'latitude_in' not in data or 'longitude_in' not in data:
                raise serializers.ValidationError("You need to specify latitude_in,longitude_in")
            else:
                distance = haversine(data['latitude_in'], data['longitude_in'], data["shift"].venue.latitude, data["shift"].venue.longitude)
                if distance > 0.1: # 0.1 miles
                    raise serializers.ValidationError("You need to be 100mt near "+data["shift"].venue.title+" to clock in or out")
                    
            # previous clockin opened
            clockins = Clockin.objects.filter(ended_at=None, employee=data["employee"])
            if len(clockins) > 0:
                raise serializers.ValidationError("You need to clock out first from all your previous shifts before attempting to clockin again")

        elif 'ended_at' in data:
            if 'latitude_out' not in data or 'longitude_out' not in data:
                raise serializers.ValidationError("You need to specify latitude_out,longitude_out")
            else:
                distance = haversine(data['latitude_out'], data['longitude_out'], data["shift"].venue.latitude, data["shift"].venue.longitude)
                if distance > 0.1: # 0.1 miles
                    raise serializers.ValidationError("You need to be 100mt near "+data["shift"].venue.title+" to clock in or out")
                    
            try:
                clockin = Clockin.objects.get(shift=data["shift"], employee=data["employee"])
            except Clockin.DoesNotExist:
                raise serializers.ValidationError("You have not clocked in yet or the shift does not exists")
                
            if clockin.started_at == None:
                raise serializers.ValidationError("You need to clock in first to this shift")
            if clockin.ended_at != None:
                raise serializers.ValidationError("You have already check out of this shift")
        
        if 'started_at' in data and 'ended_at' in data:
            raise serializers.ValidationError("You cannot clock in and out at the same time, you need to specify only the started or ended time, but not both at the same time")
            
        if 'started_at' not in data and 'ended_at' not in data:
            raise serializers.ValidationError("You need to specify the started or ended time")
        
        return data

class ClockinGetSerializer(serializers.ModelSerializer):
    shift = shift_serializer.ShiftGetSmallSerializer()
    employee = employee_serializer.EmployeeGetSmallSerializer()

    class Meta:
        model = Clockin
        exclude = ()
        

class ClockinPayrollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clockin
        exclude = ()
        
    def validate(self, data):
        
        if 'started_at' not in data and 'ended_at' not in data:
            raise serializers.ValidationError("You need to specify the started or ended time")
                
        return data