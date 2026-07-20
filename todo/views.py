from django.shortcuts import render, redirect, get_object_or_404
from .models import Task
from django.contrib.auth.decorators import login_required
from django.utils import timezone


@login_required
def task_list(request):
    tasks = Task.objects.filter(user=request.user).order_by('completed', '-created_at')
    return render(request, 'todo/task_list.html', {'tasks': tasks})


@login_required
def task_create(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()

        if title:
            Task.objects.create(user=request.user, title=title, description=description)
            return redirect('todo:list')  # redirect-after-POST prevents resubmitting the form on page refresh

    return render(request, 'todo/task_form.html')


@login_required
def task_toggle_complete(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.completed = not task.completed
    if task.completed:
        task.completed_at = timezone.now()
    else:
        task.completed_at = None
    task.save()
    return redirect('todo:list')


@login_required
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    if request.method == 'POST':
        task.delete()
        return redirect('todo:list')
    return render(request, 'todo/task_confirm_delete.html', {'task': task})