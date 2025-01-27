from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db.models import Q, BooleanField, Case, Count, F, Value, When
from django.http import HttpRequest, JsonResponse
import re
import decimal
import requests
import cloudinary
import cloudinary.api
import cloudinary.uploader
import datetime
import json
import logging
import stripe
import os

from django.contrib.auth.models import User
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.mixins import EmployerView
from api.models import (
    BankAccount, Clockin, Employee, EmployeePayment, FavoriteList, EmployerUsers, Employer, W4Form,I9Form,EmployeeDocument,
    PaymentTransaction, PayrollPeriod, PayrollPeriodPayment, Rate, Position,
    Shift, ShiftApplication, ShiftInvite, Venue,
    APPROVED, PAID, SHIFT_STATUS_CHOICES, SHIFT_INVITE_STATUS_CHOICES, OPEN,
    Shift, ShiftApplication, Employee, Profile, Payrates,
    ShiftInvite, Venue, FavoriteList,
    PayrollPeriod, Rate, Clockin, PayrollPeriodPayment, PERIOD_STATUS,
    SHIFT_STATUS_CHOICES, SHIFT_INVITE_STATUS_CHOICES,
    EmployerSubscription, EMPLOYER_STATUS, SubscriptionPlan, UserProfile, Payment
)

from api.utils import validators
from api.pagination import HeaderLimitOffsetPagination

from api.serializers import (
    employer_serializer, user_serializer, shift_serializer,
    payment_serializer, venue_serializer, favlist_serializer,
    employee_serializer, clockin_serializer, rating_serializer,
    profile_serializer, other_serializer, documents_serializer, subscription_payment_serializer,
)
from api.utils import validators
from api.utils.utils import DecimalEncoder
from django.contrib import admin
from dateutil import parser

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stream = logging.StreamHandler()
stream.setLevel(logging.DEBUG)
streamformat = logging.Formatter("%(levelname)s:%(module)s:%(message)s")
stream.setFormatter(streamformat)

logger.addHandler(stream)


DATE_FORMAT = '%Y-%m-%d'
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')


class UpdateEmployeeEmployabilityExpirationDateView(EmployerView):
    def put(self, request, *args, **kwargs):
        EmployabilityExpirationDate = request.data["catalog"]["employee"]["employability_expired_at"]
        EmployabilityExpirationDate = parser.parse(EmployabilityExpirationDate)
        EmployabilityExpirationDate = EmployabilityExpirationDate.replace(hour=0, minute=0, second=0, microsecond=0)
        employee = Employee.objects.get(id=request.data["catalog"]["employee"]["id"])
        employee.employability_expired_at = EmployabilityExpirationDate
        employee.save()
        
        return Response(status=status.HTTP_200_OK)

class EmployeeUpdateVerificationStatusView(EmployerView):
    def put(self, request, *args, **kwargs):
        employee = Employee.objects.get(id=request.data["catalog"]["employee"]["id"])
        employee.employment_verification_status = request.data["catalog"]["employee"]["employment_verification_status"]
        employee.save()
        
        return Response(status=status.HTTP_200_OK)

class EmployerMeView(EmployerView):
    def get(self, request):
        serializer = employer_serializer.EmployerGetSerializer(
            request.user.profile.employer, many=False)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, employer_id=None):
        serializer = employer_serializer.EmployerSerializer(
            request.user.profile.employer, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployerMeImageView(EmployerView):

    def put(self, request):

        if 'image' not in request.FILES:
            return Response(
                validators.error_object('No image to update'),
                status=status.HTTP_400_BAD_REQUEST)

        result = cloudinary.uploader.upload(
            request.FILES['image']
            # public_id='employer' + str(self.employer.id),
            # crop='limit',
            # width=450,
            # height=450,
            # eager=[{
            #     'width': 200, 'height': 200,
            #     'crop': 'thumb', 'gravity': 'face',
            #     'radius': 100
            # },
            # ],
            # tags=['employer_profile_picture']
        )


        self.employer.picture = result['secure_url']
        self.employer.save()
        serializer = employer_serializer.EmployerGetSerializer(self.employer)

        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployerMeUsersView(EmployerView):
    def get_queryset(self):
        # return User.objects.filter(profile__employer_id=self.employer.id)
        return User.objects.filter(Q(profile__employer_id=self.employer.id) | Q(profile__other_employers=self.employer.id) )

    def get(self, request, profile_id=False):
       
        # no hay un endpoint que use esto.
        # if id:
        #     try:
        #         qs = qs.get(id=id)
        #         many = False
        #     except User.DoesNotExist:
        #         return Response(validators.error_object(
        #             'Not found.'), status=status.HTTP_404_NOT_FOUND)
        if profile_id is not False:
                try:
                    user = User.objects.get(profile__id=profile_id)
                except User.DoesNotExist:
                    return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

                serializer = user_serializer.UserGetSmallSerializer(user, many=False)
                return Response(serializer.data, status=status.HTTP_200_OK)
        else: 
            qs = self.get_queryset()
            many = True
            serializer = user_serializer.UserGetSmallSerializer(qs, many=many)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, profile_id):

        try:
            user = self.get_queryset().get(profile__id=profile_id)
        except User.DoesNotExist:
            return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

       
        if 'employer_id' in request.data:
            employer_id = request.data['employer_id']
            employer_role = request.data['employer_role']
            try:
                employers = EmployerUsers.objects.get(profile=user.profile, employer=employer_id)
            except EmployerUsers.DoesNotExist:
                employers = None
            
            if employers is not None: 
                employers.employer_role = employer_role
                employers.save()

        serializer = profile_serializer.ProfileSerializer(user.profile, data=request.data, context={"request": request})
        
        if serializer.is_valid():
            serializer.save()
            serializer = user_serializer.UserGetSmallSerializer(user, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, profile_id):

        qs = self.get_queryset()
        try:
            user = qs.get(profile__id=profile_id)

            other_employers = User.objects.filter(profile__other_employers=self.employer.id)

            if user.profile.shift_set.count() > 0 or user.profile.shiftinvite_set.count() > 0 or user.profile.jobcoreinvite_set.count() > 0 or user.profile.rate_set.count() > 0:
                user.status = 'DELETED'
                user.save()
            elif user.profile.employee is not None:
                if not other_employers:
                    user.profile.employer = None
                    user.profile.save()
                else:
                    other_employer = EmployerUsers.objects.get(employer=self.employer.id)
                    other_employer.delete()        

            elif other_employers:
                other_employer = EmployerUsers.objects.get(employer=self.employer.id)
                other_employer.delete()
            else:
                user.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except User.DoesNotExist:
            return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)


class ApplicantsView(EmployerView):
    def get_queryset(self):
        return ShiftApplication.objects.filter(
            shift__employer_id=self.employer.id).select_related(
            'employee', 'shift')

    def fetch_list(self, request):
        lookup = {}
        return self.get_queryset().filter(**lookup)

    def get(self, request, application_id=False):
        qs = self.get_queryset()
        many = True
        if application_id:
            try:
                qs = qs.get(id=application_id)
                many = False
            except ShiftApplication.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)
        else:
            application = self.fetch_list(request)

        serializer = shift_serializer.ApplicantGetSmallSerializer(
            qs, many=many)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, application_id):
        qs = self.get_queryset()
        try:
            qs = qs.get(id=application_id)
        except ShiftApplication.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        qs.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployerShiftInviteView(EmployerView):
    def get_queryset(self):
        return ShiftInvite.objects.filter(sender__employer_id=self.employer.id)

    def fetch_one(self, request, id):
        return self.get_queryset().filter(id=id)

    def fetch_list(self, request):
        lookup = {}

        if 'status' in self.request.GET:
            status = request.GET.get('status').upper()
            available_statuses = dict(SHIFT_INVITE_STATUS_CHOICES)

            if status not in available_statuses:
                valid_choices = '", "'.join(available_statuses.keys())

                raise ValidationError({
                    'status': 'Not a valid status, valid choices are: "{}"'.format(valid_choices)  # NOQA
                })
            lookup['status'] = status

        if 'employee' in self.request.GET:
            employee = self.request.GET.get('employee')
            lookup['employee_id'] = employee

        if 'shift' in self.request.GET:
            shift = self.request.GET.get('shift')
            lookup['shift_id'] = shift

        return self.get_queryset().filter(**lookup).order_by('-created_at')

    def get(self, request, id=False):

        data = None
        single = bool(id)
        many = not (single)

        if single:
            try:
                data = self.fetch_one(request, id).get()
            except ShiftInvite.DoesNotExist:
                return Response(
                    validators.error_object(
                        'The invite was not found, maybe the shift does not exist anymore. Talk to the employer for any more details about this error.'),
                    # NOQA
                    status=status.HTTP_404_NOT_FOUND)
        else:
            data = self.fetch_list(request)

        serializer = shift_serializer.ShiftInviteGetSerializer(
            data, many=many)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, **kwargs):
        invites = []

        shifts = request.data['shifts']

        employees = None
        if 'employees' in request.data:
            employees = request.data['employees']
        elif 'employee' in request.data:
            employees = request.data['employee']
        else:
            return Response(validators.error_object('Missing employees for the invite'), status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(shifts, list):
            shifts = [shifts]

        if not isinstance(employees, list):
            employees = [employees]

        for shift in shifts:
            for employee in employees:
                data = {
                    "employee": employee,
                    "sender": request.user.profile.id,
                    "shift": shift,
                    "manually_created": True
                }
                         

                serializer = shift_serializer.ShiftCreateInviteSerializer(
                    data=data,
                    context={
                        "request": request
                    })
                if not serializer.is_valid():
                    return Response(
                        serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST
                    )

                serializer.save()
                invites.append(serializer.data)

        return Response(invites, status=status.HTTP_201_CREATED)

    def delete(self, request, id):

        try:
            invite = self.fetch_one(request, id).get()
        except ShiftInvite.DoesNotExist:
            return Response(
                validators.error_object(
                    'The invite was not found, maybe the shift does not exist anymore. Talk to the employer for any more details about this error.'),
                # NOQA
                status=status.HTTP_404_NOT_FOUND)

        invite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployerVenueView(EmployerView):
    def get_queryset(self):
        return Venue.objects.filter(employer_id=self.employer.id).order_by('title')

    def get(self, request, id=False):
        qs = self.get_queryset()
        many = True
        if id:
            try:
                qs = qs.get(id=id)
                many = False
            except Venue.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)
        else:
            qs = qs.filter(status='ACTIVE')

        serializer = venue_serializer.VenueSerializer(qs, many=many)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        request_data = request.data.copy()

        request_data['employer'] = self.employer.id
        serializer = venue_serializer.VenueSerializer(data=request_data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, id):

        try:
            venue = self.get_queryset().get(id=id)
        except Venue.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = venue_serializer.VenueSerializer(venue, data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):

        try:
            venue = self.get_queryset().get(id=id)
        except Venue.DoesNotExist:
            return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)
        
        count = venue.shift_set.count()
        if count == 0:
            venue.delete()
        else:
            venue.status = "DELETED"
            venue.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

class EmployerMeSubscriptionView(EmployerView):
    def get_queryset(self):
        return EmployerSubscription.objects.filter(employer_id=self.employer.id).order_by('-due_at')

    def get(self, request, id=False):
        qs = self.get_queryset()

        qStatus = request.GET.get('status')
        if validators.in_choices(qStatus, EMPLOYER_STATUS):
            qs = qs.filter(status=qStatus)
        else:
            qs = qs.filter(status='ACTIVE')

        serializer = other_serializer.EmployerSubscriptionPost(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        request.data['employer'] = self.employer.id
        serializer = other_serializer.EmployerSubscriptionPost(data=request.data, context={"request": request})
        all_userprofiles = UserProfile.objects.all()
        all_user_emails = list(map(lambda userprofile: userprofile, all_userprofiles))
        all_cus = list(map(lambda userprofile: userprofile.stripe_customer_id, all_userprofiles))          
        employer_email = request.data['email']
        all_emails_to_strings = [str(x) for x in all_user_emails]
        if (employer_email in all_emails_to_strings):
            cus = all_emails_to_strings.index(employer_email)
            current_cus = all_cus[cus]
        else: 
            return Response({"message": "An error has occurred, the subscription has not been created"}, status=status.HTTP_400_BAD_REQUEST)
        
        if serializer.is_valid():
            # if not 'stripe_cus' in request.data:
                # customer = subscription_payment_serializer.
                # customer = stripe.Customer.create(
                #     description=request.data['description'],
                #     email=request.data['email'],
                #     name=request.data['name'],
                #     source=request.data['source']['id'],
                #     address=request.data['address'],
                #     phone=request.data['phone']
                # )
            # else: 
                # customer = stripe.Customer.retrieve(request.data['stripe_cus'])
                # if 
            customer = stripe.Customer.retrieve(current_cus)
            
            plan = ''

            if request.data['subscription'] == 1:
                plan = 'price_1GuIrZAQGSNQlybY41AJDfoW'
                # plan = 'price_1KgEeuAQGSNQlybYFtK9Z8Jh' 
            elif request.data['subscription'] == 2:
                plan = 'price_1GuIttAQGSNQlybYWpGxUJyV'
                # plan = 'price_1KgEeTAQGSNQlybY1otsT6R6'
            elif request.data['subscription'] == 3:
                plan = 'price_1GuIv1AQGSNQlybYK7k61xh2'
                # plan = 'price_1KgEeJAQGSNQlybYmA6BmxwV'

            subscription = ''

            if customer is not None:
                if 'stripe_sub' in request.data:
                    stripe.Subscription.delete(request.data['stripe_sub'])

                subscription = stripe.Subscription.create(
                customer=customer,
                items=[
                    {"price": plan},
                ],
                )
            
            serializer.save(stripe_cus = customer.id,  stripe_sub = subscription.id)
            user = User.objects.get(email=employer_email)
            userprofile = UserProfile.objects.get(user=user)
            userprofile.stripe_sub_id = subscription.id
            userprofile.save()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
       
        plan = EmployerSubscription.objects.filter(status='ACTIVE', employer=self.employer.id).first()
        _serializer = other_serializer.SubscriptionSerializer(plan.subscription, many=False)
        return Response(_serializer.data, status=status.HTTP_201_CREATED)

class Subscription_authView(EmployerView):
    def get(self, request, email, *args, **kwargs):
        string = str(email)
        email = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', string)
        email = email.group(0)
        user = User.objects.get(email=email)
        employer = user.profile.employer
        paid_once = UserProfile.objects.filter(user=user)
        if paid_once:
            userprofile = UserProfile.objects.get(user=user)
            sub = userprofile.stripe_sub_id
            subscription_auth = stripe.Subscription.retrieve(sub)    
            sub_status = subscription_auth.status
            if sub_status == 'active' or sub_status == 'trialing':
                # employer.active_subscription = sub_status
                # employer.save()
                return Response({"message": "the subscription is active"}, status=status.HTTP_200_OK)
            else: 
                # employer.active_subscription = sub_status
                # employer.save()
                return Response({"message": "An error has occurred, the subscription is not active"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "redirecting to the subscription view for you to choose a plan"}, status=status.HTTP_200_OK)

class FavListView(EmployerView):
    def get_queryset(self):
        return FavoriteList.objects.filter(employer_id=self.employer.id)

    def get(self, request, id=False):
        qs = self.get_queryset()
        many = True

        if (id):
            try:
                qs = qs.get(id=id)
                many = False
            except FavoriteList.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = favlist_serializer.FavoriteListGetSerializer(
            qs, many=many)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):

        request.data['employer'] = self.employer.id
        serializer = favlist_serializer.FavoriteListPostSerializer(
            data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, id):

        try:
            favList = self.get_queryset().get(id=id)
        except FavoriteList.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = favlist_serializer.FavoriteListSerializer(
            favList, data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        serializedFavlist = favlist_serializer.FavoriteListGetSerializer(
            favList)
        return Response(serializedFavlist.data, status=status.HTTP_200_OK)

    def delete(self, request, id):

        try:
            favList = self.get_queryset().get(id=id)
        except FavoriteList.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        favList.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavListEmployeeView(EmployerView):
    def put(self, request, employee_id):

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = employee_serializer.EmployeeFavlistSerializer(
            employee, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
       
      
class EmployerShiftView(EmployerView, HeaderLimitOffsetPagination):
    def get(self, request, id=False):
        if id:
            try:
                shift = Shift.objects.get(id=id, employer_id=self.employer.id)
            except Shift.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = shift_serializer.ShiftGetSerializer(shift, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:

        
            shifts = Shift.objects.filter(employer_id=self.employer.id)

            qStatus = request.GET.get('status')
            if validators.in_choices(qStatus, SHIFT_STATUS_CHOICES):
                return Response(validators.error_object(
                    "Invalid Status"), status=status.HTTP_400_BAD_REQUEST)
            elif qStatus:
                status_list = qStatus.split(",")
                shifts = shifts.filter(status__in=list(map(lambda s: s.upper(), status_list)))
                if OPEN in status_list and 'filled' not in request.GET.keys():
                    shifts = shifts.annotate(total_employees=Count('employees')).exclude(
                        total_employees=F('maximum_allowed_employees')
                    )
            else:
                shifts = shifts.exclude(status='CANCELLED')

            qFilled = request.GET.get('filled')
            if qFilled == 'true':
                shifts = shifts.annotate(total_employees=Count('employees'))\
                    .filter(total_employees=F('maximum_allowed_employees'))
            elif qFilled == 'false':
                shifts = shifts.annotate(total_employees=Count('employees'))\
                    .exclude(total_employees=F('maximum_allowed_employees'))

            qStatus = request.GET.get('not_status')
            if validators.in_choices(qStatus, SHIFT_STATUS_CHOICES):
                return Response(validators.error_object(
                    "Invalid Status"), status=status.HTTP_400_BAD_REQUEST)
            elif qStatus:
                shifts = shifts.filter(~Q(status=qStatus.upper()))

            TODAY = datetime.datetime.now(tz=timezone.utc)
            qUpcoming = request.GET.get('upcoming')
            if qUpcoming == 'true':
                shifts = shifts.filter(starting_at__gte=TODAY)

            qStart = request.GET.get('start')
            if qStart is not None and qStart != '':
                start = timezone.make_aware(datetime.datetime.strptime(qStart, DATE_FORMAT))
                shifts = shifts.filter(starting_at__gte=start)

            qEnd = request.GET.get('end')
            if qEnd is not None and qEnd != '':
                end = timezone.make_aware(datetime.datetime.strptime(qEnd, DATE_FORMAT) + datetime.timedelta(days=1))
                shifts = shifts.filter(ending_at__lte=end)

            qUnrated = request.GET.get('unrated')
            if qUnrated is not None and qUnrated == 'true':
                shifts = shifts.exclude(rating=None)

            qEmployeeNot = request.GET.get('employee_not')
            if qEmployeeNot is not None:
                emp_list = qEmployeeNot.split(',')
                shifts = shifts.exclude(employees__in=[int(emp) for emp in emp_list])

            qEmployee = request.GET.get('employee')
            if qEmployee is not None:
                emp_list = qEmployee.split(',')
                shifts = shifts.filter(employees__in=[int(emp) for emp in emp_list])

            qVenue = request.GET.get('venue')
            if qVenue:
                venue_list = qVenue.split(',')
                shifts = shifts.filter(venue__in=[int(v) for v in venue_list])

            qPosition = request.GET.get('position')
            if qPosition:
                position_list = qPosition.split(',')
                shifts = shifts.filter(position__in=[int(p) for p in position_list])

            qCandidateNot = request.GET.get('candidate_not')
            if qCandidateNot is not None:
                emp_list = qCandidateNot.split(',')
                shifts = shifts.exclude(candidates__in=[int(emp) for emp in emp_list])

            shifts = shifts.select_related('venue', 'position')
            paginator = HeaderLimitOffsetPagination()
            page = paginator.paginate_queryset(shifts.order_by('-starting_at'), request)

            defaultSerializer = shift_serializer.ShiftGetSmallSerializer
            
         
            qSerializer = request.GET.get('serializer')
            if qSerializer is not None and qSerializer == "big":
                defaultSerializer = shift_serializer.ShiftGetBigListSerializer

            if page is not None:
                
                serializer = defaultSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):

        _all_serializers = []
        request.data["employer"] = self.employer.id
        if 'multiple_dates' in request.data:
            for date in request.data['multiple_dates']:
                shift_date = dict(date)
                data = dict(request.data)
                data["starting_at"] = shift_date['starting_at']
                data["ending_at"] = shift_date['ending_at']
                data.pop('multiple_dates', None)
                serializer = shift_serializer.ShiftPostSerializer( data=data, context={"request": request})
                if serializer.is_valid():
                    _all_serializers.append(serializer)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = shift_serializer.ShiftPostSerializer( data=request.data, context={"request": request})
            if serializer.is_valid():
                _all_serializers.append(serializer)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        _shifts = []
        for s in _all_serializers:
            s.save()
            return_serializer = shift_serializer.ShiftGetSerializer(s.instance, many=False)
            _shifts.append(return_serializer.data)

        return Response(_shifts, status=status.HTTP_201_CREATED)

    def put(self, request, id):

        try:
            shift = Shift.objects.get(id=id, employer__id=self.employer.id)
        except Shift.DoesNotExist:
            return Response({ "detail": "This shift was not found" },
                            status=status.HTTP_404_NOT_FOUND)

        serializer = shift_serializer.ShiftUpdateSerializer(
            shift, data=request.data, context={ "request": request })

        posponed = request.GET.get('posponed')
        if serializer.is_valid():
            # if posponed=true it will not  save, just validate
            if posponed != 'true':
                serializer.save()
                # return_serializer = shift_serializer.ShiftGetSerializer(serializer.instance, many=False)
            return Response(shift_serializer.ShiftGetSerializer(serializer.instance, many=False).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):

        try:
            shift = Shift.objects.get(id=id, employer__id=self.employer.id)
        except Shift.DoesNotExist:
            return Response(
                {
                    "detail": "This shift was not found, talk to the employer for any more details about what happened."},
                status=status.HTTP_404_NOT_FOUND)

        shift.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployerShiftNewView(EmployerView, HeaderLimitOffsetPagination):
    def get(self, request, id=None):
        if id:
            try:
                shift = Shift.objects.get(id=id, employer_id=self.employer.id)
            except Shift.DoesNotExist:
                return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)
            serializer = shift_serializer.ShiftGetSerializer(shift, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            shifts = Shift.objects.filter(employer_id=self.employer.id)

            qStatus = request.GET.get('status')
            if qStatus is None:
                shifts = shifts.exclude(status='CANCELLED')
            else:
                status_list = list(map(lambda s: s.upper(), qStatus.split(",")))
                if not validators.list_in_value_choices(status_list, SHIFT_STATUS_CHOICES):
                    return Response(validators.error_object(
                        "Invalid Status"), status=status.HTTP_400_BAD_REQUEST)
                if status_list:
                    shifts = shifts.filter(status__in=status_list)
                    if OPEN in status_list and 'filled' not in request.GET.keys():
                        shifts = shifts.annotate(total_employees=Count('employees')).exclude(
                            total_employees=F('maximum_allowed_employees')
                        )

            qFilled = request.GET.get('filled')
            if qFilled == 'true':
                shifts = shifts.annotate(total_employees=Count('employees')).filter(
                    total_employees=F('maximum_allowed_employees')
                )
            elif qFilled == 'false':
                shifts = shifts.annotate(total_employees=Count('employees')).exclude(
                    total_employees=F('maximum_allowed_employees')
                )

            qStatus = request.GET.get('not_status')
            if qStatus is not None:
                qStatus = qStatus.upper()
                if not validators.in_value_choices(qStatus, SHIFT_STATUS_CHOICES):
                    return Response(validators.error_object(
                        "Invalid Status"), status=status.HTTP_400_BAD_REQUEST)
                else:
                    shifts = shifts.filter(~Q(status=qStatus))

            TODAY = datetime.datetime.now(tz=timezone.utc)
            qUpcoming = request.GET.get('upcoming')
            if qUpcoming == 'true':
                shifts = shifts.filter(starting_at__gte=TODAY)

            qStart = request.GET.get('start')
            if qStart is not None and qStart != '':
                start = timezone.make_aware(datetime.datetime.strptime(qStart, DATE_FORMAT))
                shifts = shifts.filter(starting_at__gte=start)

            qEnd = request.GET.get('end')
            if qEnd is not None and qEnd != '':
                end = timezone.make_aware(datetime.datetime.strptime(qEnd, DATE_FORMAT) + datetime.timedelta(days=1))
                shifts = shifts.filter(ending_at__lte=end)

            qUnrated = request.GET.get('unrated')
            if qUnrated is not None and qUnrated == 'true':
                shifts = shifts.exclude(rating=None)

            qEmployeeNot = request.GET.get('employee_not')
            if qEmployeeNot is not None:
                emp_list = qEmployeeNot.split(',')
                shifts = shifts.exclude(employees__in=[int(emp) for emp in emp_list])

            qEmployee = request.GET.get('employee')
            if qEmployee is not None:
                emp_list = qEmployee.split(',')
                shifts = shifts.filter(employees__in=[int(emp) for emp in emp_list])

            qCandidateNot = request.GET.get('candidate_not')
            if qCandidateNot is not None:
                emp_list = qCandidateNot.split(',')
                shifts = shifts.exclude(candidates__in=[int(emp) for emp in emp_list])

            shifts = shifts.select_related('venue', 'position')
            paginator = HeaderLimitOffsetPagination()
            page = paginator.paginate_queryset(shifts.order_by('-starting_at'), request)

            defaultSerializer = shift_serializer.ShiftGetSmallSerializer
            qSerializer = request.GET.get('serializer')
            if qSerializer is not None and qSerializer == "big":
                defaultSerializer = shift_serializer.ShiftGetBigListSerializer

            if page is not None:
                serializer = defaultSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                return Response({'details': 'Wrong page value: None'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        _all_serializers = []
        request.data["employer"] = self.employer.id
        if 'multiple_dates' in request.data:
            for date in request.data['multiple_dates']:
                shift_date = dict(date)
                data = dict(request.data)
                data["starting_at"] = shift_date['starting_at']
                data["ending_at"] = shift_date['ending_at']
                data.pop('multiple_dates', None)
                serializer = shift_serializer.ShiftPostSerializer( data=data, context={"request": request})
                if serializer.is_valid():
                    _all_serializers.append(serializer)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = shift_serializer.ShiftPostSerializer(data=request.data, context={"request": request})
            if serializer.is_valid():
                _all_serializers.append(serializer)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        _shifts = []
        for s in _all_serializers:
            s.save()
            return_serializer = shift_serializer.ShiftGetSerializer(s.instance, many=False)
            _shifts.append(return_serializer.data)

        return Response(_shifts, status=status.HTTP_201_CREATED)

    def put(self, request, id):
        try:
            shift = Shift.objects.get(id=id, employer__id=self.employer.id)
        except Shift.DoesNotExist:
            return Response({"detail": "This shift was not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = shift_serializer.ShiftUpdateSerializer(shift, data=request.data, context={"request": request})
        posponed = request.GET.get('posponed')
        if serializer.is_valid():
            # if posponed=true it will not  save, just validate
            if posponed != 'true':
                serializer.save()
            return Response(shift_serializer.ShiftGetSerializer(serializer.instance, many=False).data,
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            shift = Shift.objects.get(id=id, employer__id=self.employer.id)
        except Shift.DoesNotExist:
            return Response(
                {"detail": "This shift was not found, talk to the employer for any more details about what happened."},
                status=status.HTTP_404_NOT_FOUND
            )

        shift.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployerShiftCandidatesView(EmployerView):
    def put(self, request, id):
        try:
            shift = Shift.objects.get(id=id)
        except Shift.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = shift_serializer.ShiftCandidatesAndEmployeesSerializer(
            shift, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployerShiftEmployeesView(EmployerView):
    def put(self, request, id):
        try:
            shift = Shift.objects.get(id=id)
        except Shift.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = shift_serializer.ShiftCandidatesAndEmployeesSerializer(
            shift, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployerClockinsMeView(EmployerView):
    def get_queryset(self):
        return Clockin.objects.filter(shift__employer__id=self.employer.id)

    def fetch_one(self, id):
        return self.get_queryset().filter(id=id).first()

    def get(self, request, id=None):

        if id is not None:
            clockin = self.fetch_one(id)
            if clockin is None:
                return Response(
                    validators.error_object('The clockin was not found'),status=status.HTTP_404_NOT_FOUND)

            serializer = clockin_serializer.ClockinGetSerializer(clockin, many=False)
        else:
            clockins = self.get_queryset()

            qShift = request.GET.get('shift')
            if qShift:
                clockins = clockins.filter(shift__id=qShift)

            qEmployee = request.GET.get('employee')
            if qEmployee:
                clockins = clockins.filter(employee__id=qEmployee)

            qUpdated = request.GET.get('updated')
            
            if qUpdated:
                today = datetime.datetime.today()
                yesterday = today - datetime.timedelta(days=1)
                clockins = clockins.filter(updated_at__range=[yesterday, today])

            qOpen = request.GET.get('open')
            if qOpen:
                clockins = clockins.filter(ended_at__isnull=(True if qOpen == 'true' else False))

            serializer = clockin_serializer.ClockinGetSerializer(
                clockins, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployerMePayrollPeriodsView(EmployerView):

    def get(self, request, period_id=None):

        if period_id is not None:
            period = PayrollPeriod.objects.filter(id=period_id, employer_id=self.employer.id).first()
            if period is None:
                return Response(
                    validators.error_object('The payroll period was not found'),status=status.HTTP_404_NOT_FOUND)

            serializer = payment_serializer.PayrollPeriodGetSerializer(period, many=False)

            return Response(serializer.data, status=status.HTTP_200_OK)
        else:

            periods = PayrollPeriod.objects.filter(employer_id=self.employer.id)
            qStart = request.GET.get('start')
            if qStart is not None and qStart != '':
                start = timezone.make_aware(datetime.datetime.strptime(qStart, DATE_FORMAT))
                periods = periods.filter(starting_at__gte=start)

            qEnd = request.GET.get('end')
            if qEnd is not None and qEnd != '':
                end = timezone.make_aware(datetime.datetime.strptime(qEnd, DATE_FORMAT) + datetime.timedelta(days=1))
                periods = periods.filter(ending_at__lte=end)

            defaultSerializer = payment_serializer.PayrollPeriodGetTinySerializer
            
            qReports = request.GET.get('reports')
            if qReports is not None and qReports == 'True':
                defaultSerializer = payment_serializer.PayrollPeriodGetDateSerializer

            serializer = defaultSerializer(periods.order_by('-starting_at')[:52:1], many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, period_id=None):
        """This method supposed that only three status are available to PayrollPeriod: OPEN, FINALIZED, PAID"""
        if 'status' not in request.data:
            return Response(validators.error_object('You need to specify the status'), status=status.HTTP_404_NOT_FOUND)
        new_status = request.data.get('status')
        if not validators.in_value_choices(new_status, PERIOD_STATUS):
            return Response({'details': 'Wrong status value was provided'}, status=status.HTTP_400_BAD_REQUEST)

        period = PayrollPeriod.objects.filter(id=period_id, employer_id=self.employer.id).first()
        if period is None:
            return Response(validators.error_object('The payroll period was not found'),
                            status=status.HTTP_404_NOT_FOUND)

        if period.status == PAID:
            return Response({'details': 'This period has a payment done and can not be changed'},
                            status=status.HTTP_400_BAD_REQUEST)
        elif period.status == new_status:
            periodSerializer = payment_serializer.PayrollPeriodSerializer(period, many=False,
                                                                          context={"request": request})
            return Response(periodSerializer.data, status=status.HTTP_200_OK)
        else:
            periodSerializer = payment_serializer.PayrollPeriodSerializer(
                period,
                data={'status': new_status},
                many=False,
                context={"request": request}
            )
            if periodSerializer.is_valid():
                periodSerializer.save()
                return Response(periodSerializer.data, status=status.HTTP_200_OK)
            else:
                return Response(periodSerializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployerMePayrollPeriodPaymentView(EmployerView):
    def get_queryset(self):
        return PayrollPeriodPayment.objects.filter(employer_id=self.employer.id)

    def fetch_one(self, id):
        return self.get_queryset().filter(id=id).first()

    def build_lookup(self, request):
        lookup = {}

        # intentionally rewrite lookup to consider
        # employee OR employer, but not both at the same time

        qs_period = request.GET.get('period')
        if qs_period:
            lookup = {'payroll_period__id': qs_period}

        return lookup

    def get(self, request, payment_id=None):

        if payment_id is not None:
            payment = self.fetch_one(payment_id)
            if payment is None:
                return Response(
                    validators.error_object('The payroll payment was not found'),status=status.HTTP_404_NOT_FOUND)

            serializer = payment_serializer.PayrollPeriodPaymentGetSerializer(payment, many=False)
        else:
            qs = self.get_queryset()
            lookup = self.build_lookup(request)
            qs = qs.filter(**lookup)
            serializer = payment_serializer.PayrollPeriodPaymentGetSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, payment_id=None):

        payment = self.fetch_one(payment_id)
        if payment is None:
            return Response(
                validators.error_object('The payroll payment was not found'),status=status.HTTP_404_NOT_FOUND)

        serializer = payment_serializer.PayrollPeriodPaymentSerializer(
            payment, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, payment_id=None):

        serializer = payment_serializer.PayrollPeriodPaymentPostSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployerMeEmployeePaymentListView(EmployerView):
    """To get total payment amounts for employee, including deductions"""
    def get_queryset(self, period_id=None):
        qs = EmployeePayment.objects.filter(employer_id=self.employer.id)
        if period_id is not None:
            qs = qs.filter(payroll_period_id=period_id)
        return qs

    def get(self, request, period_id):
        ser_employer = payment_serializer.EmployerInfoPaymentSerializer(self.employer)
        qs = self.get_queryset(period_id).order_by('id')
        ser_payments = payment_serializer.EmployeePaymentSerializer(qs, many=True,
                                                                    context={'employer_id': self.employer.id})
        return Response({'employer': ser_employer.data, 'payroll_period': period_id, 'payments': ser_payments.data},
                        status=status.HTTP_200_OK)


class EmployerMeEmployeePaymentView(EmployerView):
    """To handle a single EmployeePayment instance"""

    def post(self, request, employee_payment_id):
        try:
            employee_payment = EmployeePayment.objects.get(id=employee_payment_id)
        except EmployeePayment.DoesNotExist:
            return Response({'error': 'There is not exist the employee payment'}, status=status.HTTP_400_BAD_REQUEST)
        if employee_payment.paid:
            return Response({'error': 'The selected employee payment can not be paid'},
                            status=status.HTTP_400_BAD_REQUEST)
        context_data = {'employee_payment': employee_payment,
                        'employer': employee_payment.employer,
                        'employer_user': employee_payment.employer.profile_set.last().user,
                        'employee_user': employee_payment.employee.profile_set.last().user}
        serializer = payment_serializer.EmployeePaymentDataSerializer(data=request.data, context=context_data)
        if serializer.is_valid():
            emp_pay_ser = payment_serializer.EmployeePaymentSerializer(employee_payment,
                                                                       context={'employer_id': self.employer.id})
            #old
            # employee_payment.deductions = emp_pay_ser.data['deductions']
            # employee_payment.deduction_list = json.loads(json.dumps(emp_pay_ser.data['deduction_list'],
            #                                                         cls=DecimalEncoder))
            
            employee_payment.deductions = request.data["deductions"]
            employee_payment.deduction_list = request.data["deductions_list"]
            employee_payment.taxes = emp_pay_ser.data['taxes']
            employee_payment.amount = decimal.Decimal(emp_pay_ser.data['earnings']) - decimal.Decimal(request.data["deductions"])
            with transaction.atomic():
                employee_payment.save()
                if serializer.validated_data['payment_type'] in [PaymentTransaction.ELECT_TRANSF,
                                                                 PaymentTransaction.FAKE]:
                    # make the payment using Stripe service
                    sender_bank_acc = BankAccount.objects.get(
                        id=serializer.validated_data['payment_data']['employer_bank_account_id'])
                    receiver_bank_acc = BankAccount.objects.get(
                        id=serializer.validated_data['payment_data']['employee_bank_account_id'])
                    if serializer.validated_data['payment_type'] == PaymentTransaction.FAKE:
                        transaction_id = 'ABC123'
                    else:
                        try:
                            charge = stripe.Charge.create(amount='{:.0f}'.format(employee_payment.amount * 100),
                                                          currency='usd',
                                                          customer=sender_bank_acc.stripe_customer_id,
                                                          source=sender_bank_acc.stripe_bankaccount_id,
                                                          transfer_data={'destination': receiver_bank_acc.stripe_account_id}
                                                          )
                        except Exception as e:
                            return Response({'details': 'Error with Stripe: ' + str(e)},
                                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                        transaction_id = charge.id
                    payment_t = PaymentTransaction.objects.create(
                        amount=employee_payment.amount,
                        sender_user=sender_bank_acc.user.user,
                        receiver_user=context_data['employee_user'],
                        payment_type=serializer.validated_data['payment_type'],
                        payment_data={"service_name": "Stripe",
                                      "sender_stripe_token": sender_bank_acc.stripe_bankaccount_id,
                                      "receiver_stripe_token": receiver_bank_acc.stripe_bankaccount_id,
                                      "transaction_id": transaction_id
                                      },
                    )
                else:
                    payment_t = PaymentTransaction.objects.create(amount=employee_payment.amount,
                                                                  sender_user=context_data['employer_user'],
                                                                  receiver_user=context_data['employee_user'],
                                                                  )
                # set status for related entries as paid
                employee_payment.payment_transaction = payment_t
                employee_payment.paid = True
                employee_payment.save()
                PayrollPeriodPayment.objects.filter(payroll_period=employee_payment.payroll_period,
                                                    employee=employee_payment.employee,
                                                    employer=employee_payment.employer,
                                                    status=APPROVED).update(status=PAID)
                employee_payment.payroll_period.status = PAID
                employee_payment.payroll_period.save()
            return Response({'message': 'success'}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployeerRateView(EmployerView):

    def get_queryset(self):
        return Rate.objects.filter(employer_id=self.employer.id)

    def build_lookup(self, request):
        lookup = {}

        # intentionally rewrite lookup to consider
        # employee OR employer, but not both at the same time

        qs_employee = request.GET.get('employee')
        if qs_employee:
            lookup = {'employee_id': qs_employee}

        qs_shift = request.GET.get('shift')
        if qs_shift:
            lookup['shift_id'] = qs_shift

        return lookup

    def get(self, request, id=False):
        many = True
        qs = self.get_queryset()
        if (id):
            try:
                qs = qs.get(id=id)
                many = False
            except Rate.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)
        else:
            lookup = self.build_lookup(request)
            qs = qs.filter(**lookup)

        serializer = rating_serializer.RatingGetSerializer(qs, many=many)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        _all_serializers = []
        request.data["employer"] = self.employer.id
        if (isinstance(request.data, list)):
            for employee in request.data:
                for shift in request.data['shift']:
                    data["employee"] = employee['employee']['id']
                    data["shift"] = shift
                    data["rating"] = employee['rating']
                    data["comments"] = employee['comments']
                    serializer = shift_serializer.ShiftPostSerializer( data=data, context={"request": request})
                    if serializer.is_valid():
                        _all_serializers.append(serializer)
                    else:
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = rating_serializer.RatingSerializer(
                data=request.data, context={"request": request})
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EmployerBatchActions(EmployerView):

    def post(self, request):

        log = []
        changes = request.data['changes']
        for entity in changes:
            for key in changes[entity]:
                shift = Shift.objects.get(id=key)
                serializer = shift_serializer.ShiftUpdateSerializer(shift, data=changes[entity][key], context={"request": request })
                if serializer.is_valid():
                    serializer.save()
                    log.append("Updating "+entity+" ")

        return Response(log, status=status.HTTP_200_OK)


class EmployerPaymentDeductionView(EmployerView):
    def get_queryset(self):
        return self.employer.deductions.all()

    def get(self, request, deduction_id=None):
        many = True
        deduction = self.get_queryset()
        if deduction_id:
            try:
                deduction = deduction.get(id=deduction_id)
                many = False
            except PaymentDeduction.DoesNotExist:
                return Response(
                    validators.error_object('The payment deduction  was not found'),status=status.HTTP_404_NOT_FOUND)
        serializer = payment_serializer.PaymentDeductionSerializer(deduction, many=many)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, deduction_id):
        deduction = self.get_queryset().filter(id=deduction_id)
        if not deduction.exists():
            try:
                deduction = PaymentDeduction.objects.get(id=deduction_id)
            except:
                return Response(
                    validators.error_object('The payment deduction  was not found'),status=status.HTTP_404_NOT_FOUND)
            self.employer.deductions.add(deduction)
        else:
            deduction = deduction.last()
        serializer = payment_serializer.PaymentDeductionSerializer(deduction, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        request.data['employer'] = self.employer.id
        serializer = payment_serializer.PaymentDeductionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EmployerMeEmployeePaymentReportView(EmployerView):

    def get_queryset(self, params):
        """Method to return required EmployeePayment queryset, based on provided parameters"""
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        period_id = params.get('period_id')
        if period_id:
            qs = EmployeePayment.objects.filter(employer=self.employer, paid=True, payroll_period_id=period_id)
        elif start_date or end_date:
            qs_periods = PayrollPeriod.objects.filter(employer=self.employer).values_list('id', flat=True)
            qs = EmployeePayment.objects.filter(employer=self.employer, paid=True, payroll_period__in=qs_periods)
            if start_date:
                qs = qs.filter(payment_transaction__created_at__date__gte=start_date)
            if end_date:
                qs = qs.filter(payment_transaction__created_at__date__lte=end_date)
        else:
            qs = EmployeePayment.objects.filter(employer=self.employer, paid=True)
        return qs

    def get(self, request):
        ser_params = payment_serializer.EmployeePaymentDatesSerializer(data=request.query_params,
                                                                       context={'employer_id': self.employer.id}
                                                                       )
        if not ser_params.is_valid():
            return Response(ser_params.errors, status=status.HTTP_400_BAD_REQUEST)
        ser = payment_serializer.EmployeePaymentReportSerializer(self.get_queryset(ser_params.data), many=True)
        return Response(ser.data, status=status.HTTP_200_OK)

class EmployerMeW4Form(EmployerView):

    def get(self, request, id=False):
        if request.user is None:
            raise PermissionDenied("You don't seem to be logged in")
            
        if (id):
            logger.debug('EmployerMeW4Form:request.user###', request.user)
            try:
                w4form = W4Form.objects.filter(employee_id=id)
                logger.debug('EmployerMeW4Form:w4form###', w4form)
            except W4Form.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = employee_serializer.EmployeeW4Serializer(w4form, many=True)
            logger.debug("EmployerMeW4Form:serializer###", serializer)
            logger.debug("EmployerMeW4Form:serializer.data###", serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK)

class EmployerMeI9Form(EmployerView):

    def get(self, request, id=False):
        if request.user is None:
            raise PermissionDenied("You don't seem to be logged in")

        if (id):
            try:
                i9form = I9Form.objects.filter(employee_id=id)
                logger.debug('EmployerMeI9Form:i9form###', i9form)
            except I9Form.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = employee_serializer.EmployeeI9Serializer(i9form, many=True)
            logger.debug('EmployerMeI9Form:serializer###', serializer)
            logger.debug('EmployerMeI9Form:serializer.data###', serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK)

     
class EmployerMeEmployeeDocument(EmployerView):

    def get(self, request, id=False):
        if request.user is None:
            raise PermissionDenied("You don't seem to be logged in")

        if (id):
            try:
                documents = EmployeeDocument.objects.filter(employee_id=id)
            except EmployeeDocument.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = documents_serializer.EmployeeDocumentGetSerializer(documents, many=True)
            return JsonResponse(serializer.data, status=200, safe=False)

class EmployerMePayrates(EmployerView):
    def get_queryset(self):
        return Payrates.objects.filter(employer_id=self.employer.id)

    def get(self, request, employer_id=False):
        request.data['employer_id'] = self.employer.id
        try:
            payrates = Payrates.objects.filter(employer_id = self.employer.id)
        except Payrates.DoesNotExist:
            return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)
        serializer = employer_serializer.EmployerPayrateGetSmallSerializer(payrates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
                
    def post(self, request, employer_id=False):
        request.data['employer'] = self.employer.id
        request.data['employee'] = request.data['employee']['value']
        serializer = employer_serializer.EmployerPayratePostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_201_CREATED)  

    def put(self, request, id):
        request.data['employer'] = self.employer.id
        request.data['employee'] = request.data['employee']['value']

        try:
            payrate = self.get_queryset().get(id=id)
        except Payrates.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = employer_serializer.EmployerPayratePutSerializer(payrate, data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save() 
        return Response(serializer.data, status=status.HTTP_200_OK)
          
    def delete(self, request, id):

        try:
            payrate = self.get_queryset().get(id=id)
        except Payrates.DoesNotExist:
            return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

        payrate.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
     
class EmployerMeEmployeePaymentDeductionReportView(EmployerMeEmployeePaymentReportView):

    def get(self, request):
        ser_params = payment_serializer.EmployeePaymentDatesSerializer(data=request.query_params,
                                                                       context={'employer_id': self.employer.id}
                                                                       )
        if not ser_params.is_valid():
            return Response(ser_params.errors, status=status.HTTP_400_BAD_REQUEST)
        ser = payment_serializer.EmployeePaymentDeductionReportSerializer(self.get_queryset(ser_params.data), many=True)
        return Response(ser.data, status=status.HTTP_200_OK)
