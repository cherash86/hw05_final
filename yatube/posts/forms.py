from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta():
        model = Post
        labels = {'group': 'Группа', 'text': 'Напишите свой пост'}
        help_texts = {'group': 'Выберите группу', 'text': 'Введите ссообщение'}
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
