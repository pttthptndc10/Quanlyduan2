"""
Reports Views — Thống kê & Xuất file Excel với Django ORM.
"""

import json
from datetime import date
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from django.shortcuts import render, redirect
from django.http import HttpResponse
from apps.tasks.models import Task
from apps.projects.models import Project
from apps.authentication.models import Profile
from apps.reports.models import ComponentBatch, ComponentFile
from django.contrib.auth.models import User
from core.utils import get_user_from_session, TASK_STATUS_LABELS, PRIORITY_LABELS


def reports_view(request):
    user = get_user_from_session(request)
    tasks = Task.objects.all()
    projects = Project.objects.all()
    profiles = Profile.objects.filter(status='active')
    today = date.today().isoformat()

    by_status = {s: 0 for s in TASK_STATUS_LABELS}
    for t in tasks:
        s = t.status
        by_status[s] = by_status.get(s, 0) + 1

    member_stats = []
    for p in profiles:
        user_tasks = tasks.filter(assignee=p.user)
        member_stats.append({
            'name': p.full_name,
            'total': user_tasks.count(),
            'done': user_tasks.filter(status='done').count(),
            'overdue': sum(1 for t in user_tasks if t.deadline and t.deadline.isoformat() < today and t.status not in ('done', 'cancelled')),
        })

    batches = ComponentBatch.objects.all().select_related('created_by__profile').order_by('-created_at')

    batch_list = [
        {
            'id': b.id,
            'name': b.name,
            'status': b.status,
            'profiles': {'full_name': b.created_by.profile.full_name if (b.created_by and hasattr(b.created_by, 'profile')) else 'Admin'}
        }
        for b in batches
    ]

    return render(request, 'reports/reports.html', {
        'by_status': by_status,
        'status_labels': TASK_STATUS_LABELS,
        'member_stats': member_stats,
        'total_projects': projects.count(),
        'batches': batch_list,
        'user': user,
    })


def create_batch(request):
    if request.method != 'POST':
        return redirect('/reports/')
    user = get_user_from_session(request)
    name = request.POST.get('name', '').strip()
    if name:
        creator = User.objects.get(id=user['id'])
        ComponentBatch.objects.create(name=name, status='active', created_by=creator)
    return redirect('/reports/')


def export_batch_excel(request, batch_id):
    try:
        batch = ComponentBatch.objects.get(id=batch_id)
    except ComponentBatch.DoesNotExist:
        return redirect('/reports/')

    files = batch.files.all().select_related('project', 'created_by__profile')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Gom Linh Kien"

    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="0891B2", end_color="0891B2", fill_type="solid")
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    thin_border = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )

    headers = ['STT', 'Dự án', 'Người nhập', 'Tên linh kiện', 'Số lượng', 'Đơn giá (VND)', 'Thành tiền (VND)', 'Link Shop', 'Ghi chú']
    ws.append(headers)

    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_center

    row_idx = 1
    total_amount = 0

    for file_obj in files:
        project_name = file_obj.project.name if file_obj.project else 'Không rõ dự án'
        creator_name = file_obj.created_by.profile.full_name if (file_obj.created_by and hasattr(file_obj.created_by, 'profile')) else 'Không rõ'
        items = file_obj.content

        for item in items:
            qty = int(item.get('quantity', 1))
            price = float(item.get('price', 0))
            line_total = qty * price
            total_amount += line_total

            row_data = [
                row_idx, project_name, creator_name,
                item.get('name', ''), qty, price, line_total,
                item.get('shop', ''), item.get('notes', ''),
            ]
            ws.append(row_data)

            current_row = ws.max_row
            ws.cell(row=current_row, column=1).alignment = align_center
            ws.cell(row=current_row, column=2).alignment = align_left
            ws.cell(row=current_row, column=3).alignment = align_left
            ws.cell(row=current_row, column=4).alignment = align_left
            ws.cell(row=current_row, column=5).alignment = align_center
            ws.cell(row=current_row, column=6).number_format = '#,##0'
            ws.cell(row=current_row, column=7).number_format = '#,##0'

            for c in range(1, len(headers) + 1):
                ws.cell(row=current_row, column=c).border = thin_border

            row_idx += 1

    # Dòng tổng cộng
    total_row = ['TỔNG CỘNG', '', '', '', '', '', total_amount, '', '']
    ws.append(total_row)
    last_row = ws.max_row
    ws.merge_cells(start_row=last_row, start_column=1, end_row=last_row, end_column=6)
    total_cell = ws.cell(row=last_row, column=1)
    total_cell.font = Font(name="Arial", size=11, bold=True, color="0891B2")
    total_cell.alignment = Alignment(horizontal="right", vertical="center")

    total_val_cell = ws.cell(row=last_row, column=7)
    total_val_cell.font = Font(name="Arial", size=11, bold=True, color="0891B2")
    total_val_cell.number_format = '#,##0'

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"GomLinhKien_{batch.name.replace(' ', '_')}.xlsx"
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def export_tasks_csv(request):
    tasks = Task.objects.all().select_related('project', 'assignee__profile')

    import csv
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="tasks_export.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['Tiêu đề', 'Dự án', 'Người thực hiện', 'Trạng thái', 'Ưu tiên', 'Tiến độ %', 'Deadline'])
    for t in tasks:
        assignee_name = t.assignee.profile.full_name if (t.assignee and hasattr(t.assignee, 'profile')) else '—'
        writer.writerow([
            t.title,
            t.project.name if t.project else '',
            assignee_name,
            TASK_STATUS_LABELS.get(t.status, t.status),
            PRIORITY_LABELS.get(t.priority, t.priority),
            t.progress,
            t.deadline.isoformat() if t.deadline else '',
        ])
    return response
