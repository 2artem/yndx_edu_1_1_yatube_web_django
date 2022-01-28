from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model


User = get_user_model()


class CreationForm(UserCreationForm):
    """Собственный класс для формы регистрации"""
    class Meta(UserCreationForm.Meta):
        model = User
        # Поля выводимые в форме, в таком же порядке
        fields = ('first_name', 'last_name', 'username', 'email')
