from django.urls import path

from user.views  import SignInView, SignUpView, MyPageMainView

urlpatterns = [
    path('/login', SignInView.as_view()),
    path('/signup', SignUpView.as_view()),
    path('/mypage', MyPageMainView.as_view()),
]