import flet as ft
import json
import os


class Task(ft.Column):
    def __init__(self, task_name, task_delete, parent_app):
        super().__init__()
        self.completed = False
        self.task_name = task_name
        self.task_delete = task_delete
        self.parent_app = parent_app
        self.priority = 2
        self.deadline = None
        
        self.priority_colors = {1: "#FF6B6B", 2: "#FFA500", 3: "#9C27B0"}
        self.priority_labels = {1: "高", 2: "中", 3: "低"}

    def build(self):
        self.display_task = ft.Checkbox(
            value=self.completed, 
            label=self.task_name, 
            on_change=self.on_check_change
        )
        self.edit_name = ft.TextField(expand=1)
        self.edit_deadline = ft.TextField(label="期限 (YYYY-MM-DD)", expand=1)
        self.edit_priority = ft.Dropdown(
            label="優先順位",
            value="2",
            options=[ft.dropdown.Option("1", "高"), ft.dropdown.Option("2", "中"), ft.dropdown.Option("3", "低")],
            expand=1
        )
        
        self.task_info = ft.Column(spacing=2)
        self.update_task_info()

        self.priority_badge = ft.Container(
            content=ft.Text(self.priority_labels[self.priority], size=11, weight="bold", color="white"),
            bgcolor=self.priority_colors[self.priority],
            padding=8,
            border_radius=16,
        )

        self.display_view = ft.Container(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(expand=1, controls=[
                        ft.Row(controls=[
                            self.display_task,
                            self.priority_badge,
                        ]),
                        self.task_info
                    ]),
                    ft.Row(
                        spacing=2,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.ARROW_UPWARD,
                                icon_color="#4ECDC4",
                                tooltip="上に移動",
                                on_click=self.move_up_click,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ARROW_DOWNWARD,
                                icon_color="#4ECDC4",
                                tooltip="下に移動",
                                on_click=self.move_down_click,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.EDIT_OUTLINED,
                                icon_color="#2196F3",
                                tooltip="編集",
                                on_click=self.edit_clicked,
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE,
                                icon_color="#FF6B6B",
                                tooltip="削除",
                                on_click=self.delete_clicked,
                            ),
                        ],
                    ),
                ],
            ),
            padding=14,
            bgcolor="#FFFFFF",
            border_radius=16,
            shadow=ft.BoxShadow(
                blur_radius=8,
                color=ft.Colors.with_opacity(0.12, ft.Colors.BLACK),
                offset=(0, 2)
            ),
            margin=8,
        )

        self.edit_view = ft.Column(
            visible=False,
            spacing=12,
            controls=[
                self.edit_name,
                self.edit_deadline,
                self.edit_priority,
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    spacing=4,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                            icon_color="#4CAF50",
                            tooltip="更新",
                            on_click=self.save_clicked,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CANCEL_OUTLINED,
                            icon_color="#FF9800",
                            tooltip="キャンセル",
                            on_click=self.cancel_clicked,
                        ),
                    ],
                ),
            ],
        )
        self.controls = [self.display_view, self.edit_view]

    def update_task_info(self):
        self.task_info.controls.clear()
        if self.deadline:
            self.task_info.controls.append(ft.Text(f"📅 {self.deadline}", size=11, color="#777777"))

    def on_check_change(self, e):
        self.completed = self.display_task.value
        self.parent_app.save_and_sort()

    def edit_clicked(self, e):
        self.edit_name.value = self.display_task.label
        self.edit_deadline.value = self.deadline or ""
        self.edit_priority.value = str(self.priority)
        self.display_view.visible = False
        self.edit_view.visible = True
        self.update()

    def save_clicked(self, e):
        self.display_task.label = self.edit_name.value
        self.deadline = self.edit_deadline.value or None
        self.priority = int(self.edit_priority.value)
        self.update_task_info()
        
        self.priority_badge.bgcolor = self.priority_colors[self.priority]
        self.priority_badge.content.value = self.priority_labels[self.priority]
        
        self.display_view.visible = True
        self.edit_view.visible = False
        self.parent_app.save_and_sort()
        self.update()

    def cancel_clicked(self, e):
        self.display_view.visible = True
        self.edit_view.visible = False
        self.update()

    def move_up_click(self, e):
        self.parent_app.move_task(self, "up")

    def move_down_click(self, e):
        self.parent_app.move_task(self, "down")

    def delete_clicked(self, e):
        self.task_delete(self)
    
    def get_sort_key(self):
        return (self.completed, self.priority)


class TodoApp(ft.Column):
    def __init__(self):
        super().__init__()
        self.tasks_file = os.path.join(os.path.dirname(__file__), "tasks.json")
    
    def build(self):
        self.new_task = ft.TextField(
            hint_text="新しいタスクを追加...",
            expand=True,
            filled=True,
            bgcolor="#F8F9FA",
            border_radius=14,
            prefix_icon=ft.Icons.ADD_CIRCLE_OUTLINE,
            border_color="#E0E0E0",
            focused_border_color="#2196F3",
        )
        self.tasks_container = ft.Column(spacing=0)

        self.filter = ft.TabBar(
            scrollable=False,
            tabs=[
                ft.Tab(label="すべて"),
                ft.Tab(label="未完了"),
                ft.Tab(label="完了"),
            ],
            label_color="#2196F3",
            unselected_label_color="#BDBDBD",
            indicator_color="#2196F3",
        )

        self.filter_tabs = ft.Tabs(
            length=3,
            selected_index=0,
            on_change=lambda e: self.update(),
            content=self.filter,
        )

        self.items_left = ft.Text("0個の未完了タスク", size=13, weight="w500", color="#555555")

        self.width = 620
        self.controls = [
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Stack(
                            controls=[
                                ft.Container(
                                    content=ft.Column(spacing=0),
                                    bgcolor="#2196F3",
                                    height=120,
                                    opacity=0.1,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Row(
                                            controls=[
                                                ft.Text(
                                                    value="📋 ToDoリスト",
                                                    size=42,
                                                    weight="w900",
                                                    color="#2196F3",
                                                ),
                                            ],
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            expand=True,
                                        ),
                                        ft.Row(
                                            controls=[
                                                ft.Text(
                                                    value="🚀 生産性を最大化するタスク管理ツール",
                                                    size=12,
                                                    color="#1976D2",
                                                    weight="w600",
                                                ),
                                            ],
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            expand=True,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=8,
                                    expand=True,
                                ),
                            ]
                        ),
                        padding=16,
                        bgcolor="#F0F7FF",
                        border_radius=20,
                        width=500,
                        shadow=ft.BoxShadow(
                            blur_radius=8,
                            color=ft.Colors.with_opacity(0.12, ft.Colors.BLUE),
                            offset=(0, 2),
                        ),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Container(
                content=ft.Row(
                    controls=[
                        self.new_task,
                        ft.FloatingActionButton(
                            icon=ft.Icons.ADD,
                            on_click=self.add_clicked,
                            bgcolor="#2196F3",
                            elevation=4,
                        ),
                    ],
                    spacing=10,
                ),
                padding=12,
            ),
            ft.Container(
                content=ft.Column(
                    spacing=14,
                    controls=[
                        ft.Container(
                            content=self.filter_tabs,
                            padding=0,
                        ),
                        ft.Container(
                            content=self.tasks_container,
                            bgcolor="#F5F7FA",
                            border_radius=16,
                            padding=4,
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                self.items_left,
                                ft.OutlinedButton(
                                    content="完了をクリア",
                                    icon=ft.Icons.DELETE_SWEEP,
                                    on_click=self.clear_clicked,
                                ),
                            ],
                        ),
                    ],
                ),
                padding=8,
            ),
        ]
        self.load_tasks()

    def add_clicked(self, e):
        if self.new_task.value:
            task = Task(self.new_task.value, self.task_delete, self)
            task.build()
            self.tasks_container.controls.append(task)
            self.new_task.value = ""
            self.save_and_sort()

    def task_delete(self, task):
        self.tasks_container.controls.remove(task)
        self.save_and_sort()

    def clear_clicked(self, e):
        for task in self.tasks_container.controls[:]:
            if task.completed:
                self.task_delete(task)

    def save_and_sort(self):
        """優先順位でタスクをソートして保存"""
        self.tasks_container.controls.sort(key=lambda t: t.get_sort_key())
        self.save_tasks()
        self.update()

    def save_tasks(self):
        """タスクをJSONファイルに保存"""
        tasks_data = []
        for task in self.tasks_container.controls:
            tasks_data.append({
                "name": task.display_task.label,
                "deadline": task.deadline,
                "priority": task.priority,
                "completed": task.completed
            })
        with open(self.tasks_file, "w") as f:
            json.dump(tasks_data, f, indent=2)

    def load_tasks(self):
        """JSONファイルからタスクを読み込む"""
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, "r") as f:
                    tasks_data = json.load(f)
                for task_data in tasks_data:
                    task = Task(task_data["name"], self.task_delete, self)
                    task.priority = task_data.get("priority", 2)
                    task.deadline = task_data.get("deadline")
                    task.completed = task_data.get("completed", False)
                    task.build()
                    self.tasks_container.controls.append(task)
            except Exception as ex:
                print(f"Load error: {ex}")

    def move_task(self, task, direction):
        """指定されたタスクを上下に移動"""
        idx = self.tasks_container.controls.index(task)
        if direction == "up" and idx > 0:
            self.tasks_container.controls[idx], self.tasks_container.controls[idx - 1] = \
                self.tasks_container.controls[idx - 1], self.tasks_container.controls[idx]
        elif direction == "down" and idx < len(self.tasks_container.controls) - 1:
            self.tasks_container.controls[idx], self.tasks_container.controls[idx + 1] = \
                self.tasks_container.controls[idx + 1], self.tasks_container.controls[idx]
        self.save_tasks()
        self.update()

    def before_update(self):
        status = self.filter.tabs[self.filter_tabs.selected_index].label
        count = 0
        for task in self.tasks_container.controls:
            task.visible = (
                status == "すべて"
                or (status == "未完了" and not task.completed)
                or (status == "完了" and task.completed)
            )
            if not task.completed:
                count += 1
        self.items_left.value = f"{count}個の未完了タスク"


def main(page: ft.Page):
    page.title = "ToDoリスト"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 16
    page.bgcolor="#FAFBFC"
    
    app = TodoApp()
    page.add(ft.SafeArea(content=app))


if __name__ == "__main__":
    ft.run(main)
