from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Task


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
            messages.success(request, f'Added {title}.')
            return redirect('todo:list')

    return render(request, 'todo/task_form.html')


@login_required
def task_toggle_complete(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.completed = not task.completed
    if task.completed:
        task.completed_at = timezone.now()
        messages.success(request, f'{task.title} marked as done.')
    else:
        task.completed_at = None
        messages.success(request, f'{task.title} reopened.')
    task.save()
    return redirect('todo:list')


@login_required
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.error(request, f"Deleted {title}.")
        return redirect('todo:list')
    return render(request, 'todo/task_confirm_delete.html', {'task': task})