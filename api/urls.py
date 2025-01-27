from django.urls import include, path
# from django.contrib.auth.views import PasswordResetConfirmView
from rest_framework_jwt.views import ObtainJSONWebToken
from api.serializers.auth_serializer import CustomJWTSerializer
from api.views.deductions_view import DeductionAPIView, DeductionDetailAPIView

from api.views.subscription_payment import (
    StripeIntentView, GetCSRFToken, StripeSingleEmployeePayment
)

from api.views.hooks import (
    DefaultAvailabilityHook, ClockOutExpiredShifts, GeneratePeriodsView,
    AddTalentsToAllPositions, RemoveEmployeesWithoutProfile
)

from api.views.general_views import (
    PasswordView, ValidateEmailView, UserView, UserRegisterView, EmployeeView,
    EmployerView, ProfileMeView, ProfileMeImageView, ProfileMeResumeView, JobCoreInviteView,
    CatalogView, RateView, BadgeView, PayrollShiftsView, ProjectedPaymentsView,
    PositionView, OnboardingView, ValidateSendEmailView, ValidateSendSMSView,ValidateSMSView, ValidateEmailCompanyView, SendCompanyInvitationView, CityView, PublicShiftView,
    AppVersionView, SubscriptionsView
)
from api.views.bank_accounts_view import BankAccountAPIView, BankAccountDetailAPIView

from api.views.admin_views import (
    EmployeeBadgesView, PayrollPeriodView, EmailView, FMCView, AdminClockinsview,
    # DocumentAdmin
)
from api.views.employee_views import (
    EmployeeMeView, EmployeeShiftInviteView, EmployeeMeShiftView, EmployeeMeRateView,
    EmployeeMeSentRatingsView, ClockinsMeView, EmployeeMeApplicationsView, 
    EmployeeAvailabilityBlockView, EmployeeDeviceMeView, EmployeeMePayrollPaymentsView, EmployeeMeI9Form,EmployeeMeW4Form
)

from api.views.documents_view import (
    EmployeeDocumentAPI, EmployeeDocumentDetailAPI, DocumentAPI
)

from api.views.employer_views import (
    EmployerMeView, EmployerMeUsersView, ApplicantsView, Subscription_authView,
    EmployerMePayrollPeriodsView, EmployerMeImageView, UpdateEmployeeEmployabilityExpirationDateView,
    EmployerShiftInviteView, EmployerVenueView, EmployeeUpdateVerificationStatusView,
    FavListView, FavListEmployeeView, EmployerShiftCandidatesView,
    EmployerShiftEmployeesView, EmployerShiftView, EmployerShiftNewView, EmployerBatchActions,
    EmployerMePayrollPeriodPaymentView, EmployerClockinsMeView,
    EmployerMeEmployeePaymentView, EmployerMeEmployeePaymentListView,
    EmployerMePayrollPeriodPaymentView, EmployerClockinsMeView, EmployerMePayrates,
    EmployerMeSubscriptionView, EmployerMeEmployeePaymentReportView, EmployerMeEmployeePaymentDeductionReportView, EmployerMeW4Form,EmployerMeI9Form, EmployerMeEmployeeDocument
)

app_name = "api"

urlpatterns = [

    #
    # PUBLIC ENDPOINTS
    #
    path('version/<str:version>', AppVersionView.as_view(), name="single-version"),
    path('version', AppVersionView.as_view(), name="version"),

    path('login', ObtainJSONWebToken.as_view(serializer_class=CustomJWTSerializer)),
    path('user', include('django.contrib.auth.urls'), name="user-auth"),
    path(
        'user/password/reset',
        PasswordView.as_view(),
        name="password-reset-email"),
    path(
        'user/email/validate',
        ValidateEmailView.as_view(),
        name="validate-email"),
    path('user/email/validate/send/<str:email>', ValidateSendEmailView.as_view(), name="validate-email-send"),
    path('user/phone_number/validate/send/<str:email>/<str:phone_number>', ValidateSendSMSView.as_view(), name="validate-phone-number-send"),
    path('user/phone_number/validate/<str:email>/<str:phone_number>/<str:code>', ValidateSMSView.as_view(), name="validate-phone-number"),
    #add user to company
    path('user/email/company/validate', ValidateEmailCompanyView.as_view(), name="validate-company-invite"),
    path('user/email/company/send/<str:email>/<int:sender>/<int:employer>/<str:employer_role>', SendCompanyInvitationView.as_view(), name="send-company-invite"),
    path('user/<int:id>', UserView.as_view(), name="id-user"),
    path('user/register', UserRegisterView.as_view(), name="register"),

    path('public/shifts', PublicShiftView.as_view(), name="get-shifts"),

    path('onboarding/views/<str:view_slug>', OnboardingView.as_view(), name="get-single-onboarding"),
    path('onboarding/views', OnboardingView.as_view(), name="get-all-oboarding"),

    path('subscriptions', SubscriptionsView.as_view(), name="get-subscription"),
    path('subscriptions/<str:id>', SubscriptionsView.as_view(), name="get-all-subscriptions"),

    #
    # FOR EVERYONE LOGGED IN
    # (execution permissions may vary depending on your privileges)
    #
    path('cities', CityView.as_view(), name='get-cities'),
    path('cities/<int:id>', CityView.as_view(), name='id-cities'),

    path('employers', EmployerView.as_view(), name="get-employers"),
    path('subscription_auth/<str:email>', Subscription_authView.as_view()),
    path(
        'employers/<int:id>',
        EmployerView.as_view(),
        name="id-employers"),

    path('profiles/me', ProfileMeView.as_view(), name="me-profiles"),

    path(
        'profiles/me/image',
        ProfileMeImageView.as_view(),
        name="me-profiles-image"),
    path(
        'profiles/me/resume',
        ProfileMeResumeView.as_view(),
        name="me-profiles-resume"),

    path(
        'jobcore-invites',
        JobCoreInviteView.as_view(),
        name="get-jcinvites"),
    path(
        'jobcore-invites/<int:id>',
        JobCoreInviteView.as_view(),
        name="id-jcinvites"),

    path(
        'catalog/<str:catalog_type>',
        CatalogView.as_view(),
        name="get-catalog"),

    path('ratings', RateView.as_view(), name="get-ratings"),
    path('ratings/<int:id>', RateView.as_view(), name="single-ratings"),

    path('badges', BadgeView.as_view(), name="get-badges"),
    path('badges/<int:id>', BadgeView.as_view(), name="id-badges"),

    # manage the badges

    path(
        'employees',
        EmployeeView.as_view(),
        name="get-employees"),
    path(
        'employees/<int:id>',
        EmployeeView.as_view(),
        name="id-employees"),

    #
    # UNCLASIFIED ENDPOINTS
    # @TODO: Classify endpoint permissions to
    #        employer, empoyee, admin, logged_in or public
    #

    # path('profiles',ProfileView.as_view(), name="get-profiles"),

    path(
        'payroll',
        PayrollShiftsView.as_view(),
        name="all-payroll"),
    path('employer/<int:employer_id>/payroll_projection',
         ProjectedPaymentsView.as_view(),
         name="employer-payroll-projection"),

    # path('image/<str:image_name>',ImageView.as_view())

    #
    # FOR THE EMPLOYER
    #

    # stripe related
    path('csrf_cookie', GetCSRFToken.as_view(), name='csrf_cookie'),
    # path('admin/', admin.site.urls),
    path('create-payment-intent', StripeIntentView.as_view(), name='create-payment-intent'),
    
    path('create-payment-single-emp', StripeSingleEmployeePayment.as_view(), name='create-payment-single-emp'),
    # path('webhooks/stripe/', stripe_webhook, name='stripe-webhook'),
    # path('cancel/', CancelView.as_view(), name='cancel'),
    # path('success/', SuccessView.as_view(), name='success'),
    # path('', ProductLandingPageView.as_view(), name='landing-page'),
    # path('create-checkout-session/<pk>/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),

    path('employers/me', EmployerMeView.as_view(), name="me-employer"),
    path('employers/me/<int:employer_id>', EmployerMeView.as_view(), name="me-employer"),
    path('employers/me/image', EmployerMeImageView.as_view(), name="me-employers-image"),
    path('employers/me/subscription', EmployerMeSubscriptionView.as_view(), name="me-employer-subscription"),
    path('employers/me/users', EmployerMeUsersView.as_view(), name="me-employer-users"),
    path('employers/me/users/<int:profile_id>', EmployerMeUsersView.as_view(), name="me-employer-single-users"),
    path(
        'employers/me/applications',
        ApplicantsView.as_view(),
        name="me-employer-get-applicants"),
    path('employers/me/applications/<int:application_id>',
         ApplicantsView.as_view(), name="me-employer-get-applicants"),
    path('employers/me/payrates', EmployerMePayrates.as_view(),
         name="me-get-payrate"),
    path(
        'employers/me/payrates/<int:id>',
        EmployerMePayrates.as_view(),
        name="me-employer-id-payrates"),
    # path(
    #     'employers/me/periods',
    #     EmployerPayrollPeriodView.as_view(),
    #     name="me-employer-periods"),
    path('employers/me/payroll-periods', EmployerMePayrollPeriodsView.as_view(), name="me-get-payroll-period"),
    path('employers/me/payment', EmployerMePayrollPeriodPaymentView.as_view(), name="me-get-payroll-payments-employer"),
    path('employers/me/payment/<int:payment_id>', EmployerMePayrollPeriodPaymentView.as_view(),
         name="me-single-payroll-payments"),
    path('employers/me/payroll-periods/<int:period_id>', EmployerMePayrollPeriodsView.as_view(),
         name="me-get-single-payroll-period"),
    path('employers/me/employee-payment-list/<int:period_id>', EmployerMeEmployeePaymentListView.as_view(),
         name='me-get-employee-payment-list'),
    path('employers/me/employee-payment/<int:employee_payment_id>', EmployerMeEmployeePaymentView.as_view(),
         name='me-get-employee-payment'),
    path('employers/me/employee-payment/report', EmployerMeEmployeePaymentReportView.as_view(),
         name='me-get-employee-payment-report'),
    path('employers/me/employee-payment/deduction-report', EmployerMeEmployeePaymentDeductionReportView.as_view(),
         name='me-get-employee-payment-deduction-report'),
    # path(
    #      'employees/<int:id>/applications',
    #      EmployeeApplicationsView.as_view(),
    #      name="employee-applications"),
    # path(
    #      'employees/<int:id>/payroll',
    #      PayrollShiftsView.as_view(),
    #      name="employee-payroll"),
    # path(
    #      'clockins/',
    #      ClockinsView.as_view(),
    #      name="all-clockins"),
    # path(
    #      'clockins/<int:clockin_id>',
    #      ClockinsView.as_view(),
    #      name="me-employees"),
    
    path(
        'employers/me/invites',
        EmployerShiftInviteView.as_view(),
        name="me-employer-get-jobinvites"),
    path(
        'employers/me/shifts/invites',
        EmployerShiftInviteView.as_view(),
        name="me-employer-get-jobinvites"),
    path(
        'employers/me/shifts/invites/<int:id>',
        EmployerShiftInviteView.as_view(),
        name="me-employer-get-jobinvites"),
    path(
        'employers/me/venues',
        EmployerVenueView.as_view(),
        name="me-employer-get-venues"),
    path(
        'employers/me/venues/<int:id>',
        EmployerVenueView.as_view(),
        name="me-employer-id-venues"),
    path(
        'employers/me/favlists',
        FavListView.as_view(),
        name="me-employer-get-favlists"),
    path(
        'employers/me/favlists/<int:id>',
        FavListView.as_view(),
        name="me-employer-id-favlists"),
    path(
        'employers/me/favlists/employee/<int:employee_id>',
        FavListEmployeeView.as_view(),
        name="me-employer-id-favlists"),
    path(
        'employers/me/shifts/<int:id>/candidates',
        EmployerShiftCandidatesView.as_view(),
        name="me-employer-update-shift-candidates"),
    path(
        'employers/me/shifts/<int:id>/employees',
        EmployerShiftEmployeesView.as_view(),
        name="me-employer-update-shift-employees"),

    path(
        'employers/me/shifts',
        EmployerShiftView.as_view(),
        name="me-employer-get-shifts"),
    path(
        'employers/me/shifts/<int:id>',
        EmployerShiftView.as_view(),
        name="me-employer-id-shifts"),

    path(
        'employers/me/new-shifts',
        EmployerShiftNewView.as_view(),
        name="me-employer-get-new-shifts"),
    path(
        'employers/me/new-shifts/<int:id>',
        EmployerShiftNewView.as_view(),
        name="me-employer-id-new-shifts"),

    # aliases from similar methods
    path(
        'employers/me/jobcore-invites',
        JobCoreInviteView.as_view(),
        name="me-employer-get-jcinvites"),
    # alias for
    path(
        'employers/me/jobcore-invites/<int:id>',
        JobCoreInviteView.as_view(),
        name="me-employer-id-jcinvites"),
    path(
        'employers/me/ratings',
        RateView.as_view(),
        name="me-employer-get-ratings"),
    path(
        'employers/me/ratings/<int:id>',
        RateView.as_view(),
        name="me-employer-single-ratings"),

    path('employers/me/clockins', EmployerClockinsMeView.as_view(), name="me-employer-clockins"),
    path('employers/me/clockins/<int:id>', EmployerClockinsMeView.as_view(), name="me-employer-single-clockins"),

    path('employers/me/batch', EmployerBatchActions.as_view(), name="me-batch-actions"),

    # Deductions
    path('employers/me/deduction', DeductionAPIView.as_view(), name="me-employer-deduction"),
    path('employers/me/deduction/<int:id>', DeductionDetailAPIView.as_view(), name="me-employer-single-deduction"),

    #
    # FOR THE TALENT
    #

    path(
        'employees/me',
        EmployeeMeView.as_view(),
        name="me-employees"),
    # path('clockins/me',PaymentMeView.as_view(), name="me-employees"),
     
    path(
        'employees/me/shifts/invites',
        EmployeeShiftInviteView.as_view(),
        name="me-employees-get-jobinvites"),
    path(
        'employees/me/shifts/invites/<int:id>',
        EmployeeShiftInviteView.as_view(),
        name="me-employees-get-jobinvites"),
    path(
        'employees/me/shifts/invites/<int:id>/<str:action>',
        EmployeeShiftInviteView.as_view(),
        name="me-employees-get-jobinvites-apply"),
    path(
        'employees/me/shifts',
        EmployeeMeShiftView.as_view(),
        name="me-employees-shift"),
    path(
        'employees/me/shifts/<int:id>',
        EmployeeMeShiftView.as_view(),
        name="me-employees-get-shift"),
    # path('employees/<int:id>/shifts',general_views.ShiftView.as_view(), name="employees-shifts"),

    path('employees/me/ratings/sent', EmployeeMeSentRatingsView.as_view(), name="me-employees-ratings-sent"),
    path('employees/me/ratings/received', EmployeeMeRateView.as_view(), name="me-employees-get-ratings"),
    path('employees/me/ratings/<int:id>', EmployeeMeRateView.as_view(), name="me-employees-single-ratings"),
    # for a single rating check GET /ratings/<int:id>

    path(
        'employees/me/clockins',
        ClockinsMeView.as_view(),
        name="me-employees-clockins"),

    path(
        'employees/me/applications',
        EmployeeMeApplicationsView.as_view(),
        name="me-employee-applications"),
    path(
        'employees/me/applications/<int:application_id>',
        EmployeeMeApplicationsView.as_view(),
        name="me-employees-single-application"),
    path(
        'employees/me/availability',
        EmployeeAvailabilityBlockView.as_view(),
        name="me-employees-availability"),
    path(
        'employees/me/availability/<int:block_id>',
        EmployeeAvailabilityBlockView.as_view(),
        name="me-employees-availability"),

    path(
        'employees/me/devices',
        EmployeeDeviceMeView.as_view(),
        name="me-employees-all-device"),
    path(
        'employees/me/devices/<str:device_id>',
        EmployeeDeviceMeView.as_view(),
        name="me-employees-device"),

    # aliases from similar endpoints
    path('employees/me/jobcore-invites', JobCoreInviteView.as_view(), name="me-employees-get-jcinvites"),
    path(
        'employees/me/jobcore-invites/<int:id>',
        JobCoreInviteView.as_view(),
        name="me-employees-id-jcinvites"),

    path('employees/me/payroll-payments', EmployeeMePayrollPaymentsView.as_view(), name="me-get-payroll-payments"),


    # EMPLOYEE I9 FORM
    path('employees/me/i9-form', EmployeeMeI9Form.as_view(), name="employee-i9form"),

    # EMPLOYEE W4 FORM
    path('employees/me/w4-form', EmployeeMeW4Form.as_view(), name="employee-w4form"),

    # EMPLOYER W4 FORM
    path('employers/me/w4-form/<int:id>', EmployerMeW4Form.as_view(), name="employee-w4form"),
    path('employers/me/i9-form/<int:id>', EmployerMeI9Form.as_view(), name="employee-i9form"),
    path('employers/me/employee-documents/<int:id>', EmployerMeEmployeeDocument.as_view(), name="employee-i9form"),


    # DOCUMENTS
    path('documents', DocumentAPI.as_view(), name="document"),
    path('employees/me/documents/<int:document_id>', EmployeeDocumentDetailAPI.as_view(),
         name="employee-document-detail"),
    path('employees/me/documents', EmployeeDocumentAPI.as_view(), name="employee-document"),

    #
    # ADMIN USE ONLY
    #
    path('employee/employability_expired_at/update/<int:employee_id>',
        UpdateEmployeeEmployabilityExpirationDateView.as_view(),
        name="employability_expired_at"),
    path('employee/employment_verification_status/update/<int:employee_id>',
        EmployeeUpdateVerificationStatusView.as_view(),
        name="employment_verification_status"),
    path('admin/clockins', AdminClockinsview.as_view(), name="admin-get-clockins"),
    path(
        'employees/<int:employee_id>/badges',
        EmployeeBadgesView.as_view(),
        name="admin-id-employees-badges"),
    # update the talent badges
    path('positions', PositionView.as_view(), name="admin-get-positions"),
    path(
        'positions/<int:id>',
        PositionView.as_view(),
        name="admin-id-positions"),
    path('periods', PayrollPeriodView.as_view(), name="admin-get-periods"),
    path(
        'periods/<int:period_id>',
        PayrollPeriodView.as_view(),
        name="admin-get-periods"),

    path('bank-accounts/', BankAccountAPIView.as_view(), name='api-bank-accounts'),
    path('bank-accounts/<int:bank_account_id>', BankAccountDetailAPIView.as_view(), name='detail-api-bank-accounts'),

    ###

    path('email/<str:slug>', EmailView.as_view()),  # test email
    path('fmc', FMCView.as_view()),  # test mobile notification

    #
    # HOOKS
    #
    path('hook/remove_employees_without_profile', RemoveEmployeesWithoutProfile.as_view()),
    path('hook/add_talents_to_all_positions', AddTalentsToAllPositions.as_view()),
    path('hook/create_default_availablity_blocks', DefaultAvailabilityHook.as_view()),

    # clocks out, deletes invites, deletes applications
    path('hook/process_expired_shifts', ClockOutExpiredShifts.as_view(), name="hook-process-expired-shifts"),
    # every 5 min

    # every hour, will generate payment periods, params:
    #   - employer: optional
    path('hook/generate_periods', GeneratePeriodsView.as_view(), name="hook-generate_periods"),

]
