from django import forms

from .models import Post
from .models import Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        # Поля выводимые в форме, в таком же порядке
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
