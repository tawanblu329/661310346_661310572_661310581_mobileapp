import flet as ft
import requests
import threading



API_URL = "http://127.0.0.1:8000"
API_URL = "http://172.30.123.207:8000"
dark_mode = {"value": False}
PRIMARY = "#4f46e5"
BG = "#f1f5f9"

def main(page: ft.Page):
    page.title = "Goodness App"
    page.bgcolor=ft.Colors.SURFACE
    page.padding = 0
    page.fonts = {
        "Kanit": "https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap"
    }

    page.theme = ft.Theme(font_family="Kanit")

    current_user = {"data": None}

    # =========================
    # APP BAR 
    # =========================
    def appbar():
        user_name = current_user["data"]["fullname"] if current_user["data"] else "Guest"
        
        return ft.AppBar(
            bgcolor=PRIMARY,
            center_title=False,
            title=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("สมุดบันทึกความดี", size=18, weight="bold", color="white"),
                        ],
                        spacing=10,
                    ),
                    
                    ft.Container(
                        content=ft.Text(
                            f"ยินดีต้อนรับ! {user_name}",
                            color="white",
                            size=14,
                            weight="w500",
                            overflow=ft.TextOverflow.ELLIPSIS, 
                            max_lines=1,
                        ),
                        expand=True,
                        alignment=ft.alignment.Alignment(1, 0), 
                        padding=ft.Padding(0, 0, 20, 0)
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        )
    
        
    def toggle_dark(e):
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
        else:
            page.theme_mode = ft.ThemeMode.DARK
        
        page.update()
    
    # =========================
    # SNACKBAR
    # =========================
    def show_snackbar(msg, success=True):
        page.snack_bar = ft.SnackBar(
            ft.Text(msg),
            bgcolor="#16a34a" if success else "#dc2626"
        )
        page.snack_bar.open = True
        page.update()

    # =========================
    # NAVBAR
    # =========================
    def bottom_nav(index=0):
        is_admin = current_user["data"] and current_user["data"].get("role") == "admin"
        
        return ft.NavigationBar(
            selected_index=index,
            bgcolor="white",
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.DASHBOARD if is_admin else ft.Icons.HOME, 
                    label="แดชบอร์ด" if is_admin else "หน้าแรก"
                ),
                ft.NavigationBarDestination(icon=ft.Icons.ADD, label="ให้คะแนน"),
                ft.NavigationBarDestination(icon=ft.Icons.CARD_GIFTCARD, label="รางวัล"),
                ft.NavigationBarDestination(icon=ft.Icons.EMOJI_EVENTS, label="จัดอันดับ"),
                ft.NavigationBarDestination(icon=ft.Icons.PERSON, label="โปรไฟล์"),
            ],
            on_change=lambda e: navigate(e.control.selected_index)
        )

    def navigate(index):
        is_admin = current_user["data"] and current_user["data"].get("role") == "admin"
        if index == 0:
            if is_admin: 
                show_admin_dashboard() 
            else: 
                show_home()
        elif index == 1:
            show_add_point()
        elif index == 2:
            show_rewards()
        elif index == 3:
            show_leaderboard()
        elif index == 4:
            show_profile()

    # =========================
    # LAYOUT TEMPLATE 
    # =========================
    
    def layout(content, nav_index):
        page.clean()
        page.appbar = appbar()

        page.add(
            ft.Column(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                content,
                            ],
                            expand=True,
                            scroll=ft.ScrollMode.AUTO  
                        ),
                        expand=True,
                        margin=ft.Margin(0, 0, 0, 20) 
                    ),

                    bottom_nav(nav_index)
                ],
                expand=True,
                spacing=0 
            )
        )

    # =========================
    # Login Screen 
    # =========================
    def show_login():
        page.clean()
        page.appbar = None  

        card_bg = "surface" 
        field_bg = "surfaceVariant" 
        text_color = "onSurface" 
        label_col = "onSurfaceVariant"

        username_field = ft.TextField(
            label="Username",
            hint_text="กรอกชื่อผู้ใช้ของคุณ",
            width=320,
            border_radius=ft.BorderRadius(15, 15, 15, 15), 
            prefix_icon=ft.Icons.PERSON_OUTLINE, 
            bgcolor=field_bg, 
            border_color="outlineVariant", 
            focused_border_color=PRIMARY,
            label_style=ft.TextStyle(color=label_col),
            text_style=ft.TextStyle(color=text_color),
        )

        password_field = ft.TextField(
            label="Password",
            hint_text="กรอกรหัสผ่านของคุณ",
            password=True,
            can_reveal_password=True,
            width=320,
            border_radius=ft.BorderRadius(15, 15, 15, 15), 
            prefix_icon=ft.Icons.LOCK_OUTLINE, 
            bgcolor=field_bg,
            border_color="outlineVariant", 
            focused_border_color=PRIMARY,
            label_style=ft.TextStyle(color=label_col),
            text_style=ft.TextStyle(color=text_color),
        )

        loading_ring = ft.ProgressRing(width=20, height=20, visible=False, color="white")
        button_text = ft.Text("เข้าสู่ระบบ", weight="bold", color="white", size=16)

        def login_click(e):
            if not username_field.value or not password_field.value:
                page.snack_bar = ft.SnackBar(
                    ft.Text("กรุณากรอก Username และ Password"),
                    bgcolor="orange"
                )
                page.snack_bar.open = True
                page.update()
                return

            login_button.disabled = True
            button_text.visible = False
            loading_ring.visible = True
            page.update()

            try:
                res = requests.post(f"{API_URL}/login", json={
                    "username": username_field.value,
                    "password": password_field.value
                }, timeout=5)

                if res.status_code == 200:
                    current_user["data"] = res.json()["user"]

                    def go_home(e):
                        dlg.open = False
                        page.update()
                        if current_user["data"]["role"] == "admin":
                            show_admin_dashboard()
                        else:
                            show_home()

                    dlg = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("✅ เข้าสู่ระบบสำเร็จ", size=16, weight="bold"),
                        content=ft.Text(f"ยินดีต้อนรับ! {current_user['data']['fullname']} 👋", size=14),
                        actions=[ft.TextButton("ตกลง", on_click=go_home)],
                        actions_alignment=ft.MainAxisAlignment.END,
                    )
                    page.overlay.append(dlg)
                    dlg.open = True
                    page.update()

                else:
                    def close_dlg(e):
                        dlg.open = False
                        page.update()

                    dlg = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("❌ เข้าสู่ระบบไม่สำเร็จ", size=16, weight="bold"),
                        content=ft.Text("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง", size=14),
                        actions=[ft.TextButton("ตกลง", on_click=close_dlg)],
                        actions_alignment=ft.MainAxisAlignment.END,
                    )
                    page.overlay.append(dlg)
                    dlg.open = True
                    page.update()

            except Exception:
                page.snack_bar = ft.SnackBar(
                    ft.Text("ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้"),
                    bgcolor="grey"
                )
                page.snack_bar.open = True
                page.update()

            finally:
                login_button.disabled = False
                button_text.visible = True
                loading_ring.visible = False
                page.update()

        def login_guest_click(e):
            current_user["data"] = {
                "username": "guest",
                "fullname": "ผู้เยี่ยมชม (Guest)",
                "total_point": 0
            }
            show_home()

        login_button = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.LOGIN, color="white"),
                    button_text,
                    loading_ring
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            width=320,
            height=55,
            style=ft.ButtonStyle(
                color="white",
                bgcolor=PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=15),
                elevation=3,
            ),
            on_click=login_click
        )

        guest_button = ft.Button(
            content=ft.Row(
                [
                    ft.Text("เข้าสู่ระบบแบบ Guest", weight="bold", color="#616161", size=16),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            width=320,
            height=55,
            style=ft.ButtonStyle(
                bgcolor="transparent", 
                shape=ft.RoundedRectangleBorder(radius=10),
                side=ft.BorderSide(1, color="#616161"), 
            ),
            on_click=login_guest_click
        )

        login_card = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.FAVORITE, color=PRIMARY, size=45),
                    ft.Text("Goodness App", size=28, weight="bold", color=PRIMARY),
                    ft.Text("บันทึกความดี สร้างแรงบันดาลใจ", size=14, color="outline"),
                    
                    ft.Container(height=10), 
                    
                    username_field,
                    password_field,
                    
                    ft.Container(height=10), 
                    
                    login_button,
                    guest_button, 
                    
                   
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12, 
                tight=True, 
            ),
            width=380, 
            padding=30, 
            border_radius=25, 
            bgcolor=card_bg, 
            border=ft.Border.all(1, "surfaceVariant"), 
            shadow=ft.BoxShadow(
                blur_radius=20, 
                spread_radius=1, 
                color="#0D000000" if page.theme_mode == ft.ThemeMode.LIGHT else "#1A000000"
            )
        )

        page.add(
            ft.Container(
                content=login_card,
                alignment=ft.Alignment(0, 0), 
                expand=True,
                bgcolor=BG,
                padding=20
            )
        )

    # =========================
    # HOME
    # =========================
                    
    def show_home():
        page.clean()
        user = current_user["data"]
        
        is_dark_mode = page.theme_mode == ft.ThemeMode.DARK

        txt_color = "white" if is_dark_mode else "black"
        sub_txt_color = "white70" if is_dark_mode else "#64748b"
        card_background = "#2d2d2d" if is_dark_mode else ft.Colors.WHITE

        total_point = user.get('total_point', 0)
        try:
            res_pts = requests.get(f"{API_URL}/user_points/{user['id']}", timeout=2)
            if res_pts.status_code == 200:
                total_point = sum(item['point'] for item in res_pts.json())
        except: pass

        banner_data = [
            {"title": "ทำดีได้แต้ม", "desc": "ช่วยเพื่อนทำความสะอาดรับ 20 แต้ม", "color": "#4f46e5", "icon": "🧹"},
            {"title": "ข่าวสารใหม่", "desc": "อัปเดตระบบจัดอันดับประจำสัปดาห์", "color": "#10b981", "icon": "📢"},
            {"title": "แลกรางวัล", "desc": "ใช้คะแนนแลกขนมที่ห้องสหกรณ์", "color": "#f59e0b", "icon": "🎁"},
        ]
        banner_row = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text(b["icon"], size=30),
                        ft.Text(b["title"], weight="bold", color="white", size=16),
                        ft.Text(b["desc"], color="white70", size=11, max_lines=2),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=2),
                    width=220, height=120, bgcolor=b["color"], padding=15, border_radius=15,
                ) for b in banner_data
            ],
            scroll=ft.ScrollMode.ADAPTIVE, spacing=15,
        )

        header_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text("สวัสดีตอนเช้า 👋", size=14, color="white70"),
                        ft.Text(user['fullname'], size=22, weight="bold", color="white"),
                    ], expand=True),
                    ft.Icon(ft.Icons.NOTIFICATIONS_OUTLINED, color="white70"),
                ]),
                ft.Divider(height=10, color="white24"),
                ft.Row([
                    ft.Column([
                        ft.Text("คะแนนสะสมของคุณ", size=12, color="white70"),
                        ft.Row([
                            ft.Text("⭐", size=20),
                            ft.Text(f"{total_point}", size=28, weight="bold", color="white"),
                            ft.Text("คะแนน", size=14, color="white70"),
                        ], vertical_alignment="end", spacing=5),
                    ]),
                    ft.Container(
                        content=ft.Text("🥈 ระดับเงิน", color="white", size=11, weight="bold"),
                        bgcolor="white24", padding=8, border_radius=10,
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]),
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                colors=[PRIMARY, "#6366f1"],
            ),
            padding=20, border_radius=25, width=float("inf"),
        )

        content = ft.Column([
            header_card,
            
            ft.Row([
                ft.Text(
                    "กิจกรรมและข่าวสาร", 
                    weight="bold", 
                    size=16, 
                    color=ft.Colors.WHITE if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.BLACK
                ),
                ft.Text("ดูทั้งหมด", size=12, color=PRIMARY),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Container(content=banner_row, margin=ft.Margin(0, -15, 0, 0)),
            
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.LIGHTBULB_CIRCLE, color="#f59e0b", size=30),
                    ft.Column([
                        ft.Text("เคล็ดลับการสะสมแต้ม", weight="bold", size=14, color=txt_color),
                        ft.Text("ร่วมกิจกรรมจิตอาสาช่วงพักเที่ยง รับแต้ม X2", size=12, color=sub_txt_color),
                    ], expand=True, spacing=0),
                ]),
                bgcolor=card_background, padding=15, border_radius=15,
                border=ft.Border.all(1, "outlineVariant" if not is_dark_mode else "white10")
            )
        ], expand=True, scroll=ft.ScrollMode.AUTO, spacing=20)

        layout(
            ft.Container(
                content=content, 
                padding=ft.Padding(20, 30, 20, 20)
            ), 
            0
        )
        
    # =========================
    # ADMIN DASHBOARD
    # =========================
    def show_admin_dashboard():
        page.clean()
        user = current_user["data"]
        
        is_dark = page.theme_mode == ft.ThemeMode.DARK
        text_col = "white" if is_dark else "black"
        card_bg = "#2d2d2d" if is_dark else "white"
        
        state = {"students": [], "recent_points": []}

        try:
            res_std = requests.get(f"{API_URL}/students", timeout=5)
            if res_std.status_code == 200:
                state["students"] = res_std.json()
                
            res_pts = requests.get(f"{API_URL}/recent_points", timeout=5)
            if res_pts.status_code == 200:
                state["recent_points"] = res_pts.json()
        except Exception as e:
            print(f"Error loading dashboard: {e}")

        feed_column = ft.Column(spacing=10)
        
        if not state["recent_points"]:
            feed_column.controls.append(ft.Text("ยังไม่มีความเคลื่อนไหว", color="grey"))
        else:
            for p in state["recent_points"]:
                is_positive = p['point'] > 0
                point_color = "#16a34a" if is_positive else "#ef4444" 
                
                icon_name = ft.Icons.CHECK_CIRCLE if is_positive else ft.Icons.REMOVE_CIRCLE
                icon_bg = "#10b981" if is_positive else "#f87171"

                feed_column.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.CircleAvatar(content=ft.Icon(icon_name, color="white", size=18), bgcolor=icon_bg, radius=20),
                            ft.Column([
                                ft.Text(f"{p['fullname']} (ห้อง {p['student_class']})", weight="bold", size=14, color=text_col),
                                ft.Text(f"{p['description']} | {p['date']}", size=12, color="grey"),
                            ], expand=True, spacing=2),
                            ft.Text(f"{point_sign}{p['point']} แต้ม", color=point_color, weight="bold", size=16)
                        ]),
                        padding=15, bgcolor=card_bg, border_radius=12,
                        border=ft.Border.all(1, "white10" if is_dark else "#e2e8f0"),
                        shadow=ft.BoxShadow(blur_radius=5, color="#0A000000") if not is_dark else None
                    )
                )

        tab_feed = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text("นักเรียนทั้งหมด", size=12, color="white70"),
                        ft.Text(f"{len(state['students'])} คน", size=24, weight="bold", color="white"),
                    ], expand=True),
                    ft.Icon(ft.Icons.GROUPS, color="white", size=40)
                ]),
                gradient=ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=[PRIMARY, "#6366f1"]),
                padding=20, border_radius=20, margin=ft.Margin(0,0,0,10)
            ),
            ft.Text("การให้คะแนนล่าสุด ⚡", size=18, weight="bold", color=text_col),
            feed_column
        ], scroll=ft.ScrollMode.AUTO, expand=True)



        student_list_ui = ft.Column(spacing=5, expand=True, scroll=ft.ScrollMode.AUTO)
        
        def show_student_profile_popup(student_info):
            total_point = 0
            history_data = []
            try:
                res = requests.get(f"{API_URL}/user_points/{student_info['id']}", timeout=5)
                if res.status_code == 200:
                    history_data = res.json()
                    total_point = sum(item['point'] for item in history_data)
            except: pass

            redeem_history_data = []
            try:
                res_redeem = requests.get(f"{API_URL}/user_redeem_history/{student_info['id']}", timeout=5)
                if res_redeem.status_code == 200:
                    redeem_history_data = res_redeem.json()
            except: pass

            list_item_bg = "surfaceVariant" if is_dark else "#f1f5f9"
            safe_username = str(student_info.get('username', student_info.get('fullname', 'student'))).replace(" ", "%20")
            avatar_url = f"https://api.dicebear.com/9.x/bottts/png?seed={safe_username}"

            def get_emoji(desc):
                desc = desc or ""
                if any(w in desc for w in ["ขยะ", "ทำความสะอาด", "กวาด"]): return "🧹"
                elif any(w in desc for w in ["เพื่อน", "ติว", "แบ่งปัน"]): return "🤝"
                else: return "⭐"

            def get_badge(pts):
                if pts >= 500: return "🥇 ระดับทอง"
                elif pts >= 200: return "🥈 ระดับเงิน"
                else: return "🌱 มือใหม่"

            positive_history = [item for item in history_data if item.get('point', 0) > 0]
            recent_controls = []
            if not positive_history:
                recent_controls.append(ft.Text("ยังไม่มีประวัติความดี", color="grey", italic=True, size=13))
            else:
                for item in positive_history[:5]:
                    recent_controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(get_emoji(item.get("description", "")), size=14),
                                ft.Text(item.get("description", "-"), size=12, expand=True, no_wrap=True), 
                                ft.Text(f"+{item['point']}", color="#16a34a", weight="bold", size=12),
                            ], spacing=8),
                            padding=8, bgcolor=list_item_bg, border_radius=8,
                        )
                    )

            redeem_controls = []
            if not redeem_history_data:
                redeem_controls.append(ft.Text("ยังไม่มีประวัติการแลกรางวัล", color="grey", italic=True, size=13))
            else:
                for item in redeem_history_data[:3]: 
                    redeem_controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Image(src=item["image"], width=30, height=30, border_radius=5, fit="cover"),
                                ft.Column([
                                    ft.Text(item["name"], size=12, weight="bold"),
                                    ft.Text(item.get("date", "-"), size=10, color="grey"),
                                ], spacing=0, expand=True),
                                ft.Text(f"-{item['point']}", color="#ef4444", weight="bold", size=12),
                            ], spacing=8),
                            padding=8, bgcolor=list_item_bg, border_radius=8,
                        )
                    )

            profile_content = ft.Column([
                ft.CircleAvatar(foreground_image_src=avatar_url, radius=40),
                ft.Text(student_info["fullname"], size=20, weight="bold", text_align="center"),
                ft.Text(f"ห้อง {student_info.get('student_class', '-')}", size=14, color="grey", text_align="center"),
                ft.Text(get_badge(total_point), size=13, color=PRIMARY, text_align="center"),
                
                ft.Container(
                    content=ft.Row([
                        ft.Text("⭐", size=20),
                        ft.Text(f"{total_point} แต้ม", size=20, weight="bold", color=PRIMARY),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                    padding=10, bgcolor="#ede9fe" if not is_dark else ft.Colors.with_opacity(0.1, PRIMARY),
                    border_radius=10,
                ),
                
                ft.Divider(height=10, color="transparent"),
                ft.Text("📋 ประวัติความดีล่าสุด", weight="bold", size=14),
                *recent_controls,
                
                ft.Divider(height=10, color="transparent"),
                ft.Text("🎁 ประวัติการแลกรางวัล", weight="bold", size=14),
                *redeem_controls,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO, spacing=5)

            def close_profile_dlg(e):
                profile_dlg.open = False
                page.update()

            profile_dlg = ft.AlertDialog(
                title=ft.Row([
                    ft.Text("โปรไฟล์นักเรียน", weight="bold", size=16),
                    ft.IconButton(ft.Icons.CLOSE, on_click=close_profile_dlg, icon_size=20)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                content=ft.Container(content=profile_content, width=320, height=450),
                title_padding=ft.Padding(20, 20, 10, 10),
                content_padding=ft.Padding(20, 0, 20, 20),
                shape=ft.RoundedRectangleBorder(radius=15),
            )
            
            page.overlay.append(profile_dlg)
            profile_dlg.open = True
            page.update()

        def render_students(search_text=""):
            student_list_ui.controls.clear()
            filtered = [s for s in state["students"] if search_text.lower() in s["fullname"].lower() or search_text in s["student_class"]]
            
            for s in filtered:
                safe_name = str(s.get('username', s.get('fullname', 'student'))).replace(" ", "%20")
                student_list_ui.controls.append(
                    ft.ListTile(
                        leading=ft.CircleAvatar(foreground_image_src=f"https://api.dicebear.com/9.x/bottts/png?seed={safe_name}"),
                        title=ft.Text(s["fullname"], weight="bold", color=text_col),
                        subtitle=ft.Text(f"ห้อง: {s['student_class']}", color="grey"),
                        bgcolor=card_bg,
                        shape=ft.RoundedRectangleBorder(radius=10),
                        on_click=lambda e, student_data=s: show_student_profile_popup(student_data)
                    )
                )
            page.update()

        render_students()

        def on_search(e):
            render_students(e.control.value)

        search_bar = ft.TextField(
            hint_text="ค้นหาชื่อ หรือ ห้องเรียน...", prefix_icon=ft.Icons.SEARCH,
            border_radius=15, bgcolor=card_bg, height=50, on_change=on_search
        )

        add_username = ft.TextField(label="Username (สำหรับล็อกอิน)")
        add_pass = ft.TextField(label="Password")
        add_name = ft.TextField(label="ชื่อ-นามสกุล")
        add_class = ft.TextField(label="ห้องเรียน (เช่น 1/1)")
        
        add_dialog = ft.AlertDialog(modal=True)

        def close_add_dlg(e=None):
            add_dialog.open = False
            page.update()

        def save_new_student(e):
            try:
                res = requests.post(f"{API_URL}/users", json={
                    "username": add_username.value,
                    "password": add_pass.value,
                    "fullname": add_name.value,
                    "role": "student",
                    "student_class": add_class.value
                })
                if res.status_code == 200:
                    page.snack_bar = ft.SnackBar(ft.Text("เพิ่มนักเรียนสำเร็จ!"), bgcolor="#16a34a")
                    page.snack_bar.open = True
                    close_add_dlg()
                    show_admin_dashboard()
                else:
                    page.snack_bar = ft.SnackBar(ft.Text("เกิดข้อผิดพลาดในการเพิ่มนักเรียน"), bgcolor="red")
                    page.snack_bar.open = True
            except Exception as ex:
                print(ex)
            page.update()

        def open_add_dialog(e):
            add_username.value = ""
            add_pass.value = ""
            add_name.value = ""
            add_class.value = ""
            
            add_dialog.title = ft.Text("➕ เพิ่มนักเรียนใหม่", weight="bold")
            add_dialog.content = ft.Column([add_username, add_pass, add_name, add_class], tight=True)
            add_dialog.actions = [
                ft.TextButton("ยกเลิก", on_click=close_add_dlg),
                ft.Button("บันทึก", bgcolor=PRIMARY, color="white", on_click=save_new_student)
            ]
            if add_dialog not in page.overlay: page.overlay.append(add_dialog)
            add_dialog.open = True
            page.update()

        tab_manage = ft.Column([
            ft.Row([
                ft.Container(content=search_bar, expand=True),
                ft.IconButton(icon=ft.Icons.PERSON_ADD_ALT_1, icon_color="white", bgcolor=PRIMARY, on_click=open_add_dialog, icon_size=24)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            student_list_ui
        ], expand=True)


        
        tab_content_area = ft.Container(content=tab_feed, padding=ft.Padding(0, 10, 0, 0), expand=True)

        def switch_tab(e):
            is_overview = (e.control.data == "overview")
            
            btn_overview.bgcolor = PRIMARY if is_overview else ft.Colors.TRANSPARENT
            btn_manage.bgcolor = ft.Colors.TRANSPARENT if is_overview else PRIMARY
            
            btn_overview.content.color = ft.Colors.WHITE if is_overview else PRIMARY
            btn_manage.content.color = PRIMARY if is_overview else ft.Colors.WHITE

            tab_content_area.content = tab_feed if is_overview else tab_manage
            page.update()

        btn_overview = ft.Container(
            content=ft.Text("ภาพรวมโรงเรียน", color=ft.Colors.WHITE, weight="bold"),
            data="overview",
            bgcolor=PRIMARY,
            padding=ft.Padding(15, 10, 15, 10),
            border_radius=8,
            on_click=switch_tab
        )
        
        btn_manage = ft.Container(
            content=ft.Text("จัดการนักเรียน", color=PRIMARY, weight="bold"),
            data="manage",
            bgcolor=ft.Colors.TRANSPARENT,
            padding=ft.Padding(15, 10, 15, 10),
            border_radius=8,
            on_click=switch_tab
        )

        custom_tabs = ft.Row([btn_overview, btn_manage], spacing=10)


        content = ft.Column([
            ft.Text("แผงควบคุมคุณครู", size=26, weight="bold", color=PRIMARY),
            custom_tabs,
            ft.Divider(height=1, color="white24" if is_dark else "black12"),
            tab_content_area
        ], expand=True)

        layout(
            ft.Container(content=content, padding=ft.Padding(20, 20, 20, 0), expand=True), 
            0
        )
        
    # =========================
    # ADD POINT, EDIT/DELETE STUDENT & ADD REWARD
    # =========================
    def show_add_point():
        students_data = []
        categories_data = []
        selected_student_id = {"value": None}

        popup_title = ft.Text("แจ้งเตือน", weight="bold")
        popup_content = ft.Text("")

        def close_popup(e):
            popup.open = False
            page.update()

        popup = ft.AlertDialog(
            title=popup_title,
            content=popup_content,
            actions=[ft.TextButton("ตกลง", on_click=close_popup)]
        )

        def show_popup(msg, success):
            popup_title.value = "🎉 สำเร็จ!" if success else "❌ เกิดข้อผิดพลาด"
            popup_title.color = "green" if success else "red"
            popup_content.value = msg
            if popup not in page.overlay:
                page.overlay.append(popup)
            popup.open = True
            page.update()

        classroom_dropdown = ft.Dropdown(
            label="1. เลือกห้องเรียน (เพื่อกรองรายชื่อ)",
            width=350,
            options=[] 
        )

        search_box = ft.TextField(
            label="2. พิมพ์ค้นหาชื่อนักเรียน...",
            width=350,
            prefix_icon="search" 
        )
        search_results = ft.Column(width=350, spacing=2, visible=False)

        card_avatar_img = ft.Image(src="")
        card_avatar = ft.CircleAvatar(content=card_avatar_img, radius=30)
        card_name = ft.Text("", size=18, weight="bold")
        card_class = ft.Text("", size=14, color="grey")

        edit_fullname_field = ft.TextField(label="ชื่อ-นามสกุลใหม่")
        edit_class_field = ft.TextField(label="ห้องเรียนใหม่ (เช่น 1/1)")
        edit_dialog = ft.AlertDialog(modal=True)

        def close_edit_dlg(e=None):
            edit_dialog.open = False
            page.update()

        def save_edit_student(e):
            s_id = selected_student_id["value"]
            if not s_id: return
            new_name = edit_fullname_field.value.strip()
            new_class = edit_class_field.value.strip()

            if not new_name or not new_class:
                show_popup("กรุณากรอกข้อมูลให้ครบถ้วน", False)
                return
            try:
                res = requests.put(f"{API_URL}/students/{s_id}", json={
                    "fullname": new_name, "student_class": new_class
                })
                if res.status_code == 200:
                    show_popup("อัปเดตข้อมูลสำเร็จ!", True)
                    close_edit_dlg()
                    fetch_students() 
                    select_student(s_id, new_name, new_class)
                else:
                    show_popup("เกิดข้อผิดพลาดในการอัปเดต", False)
            except Exception as ex:
                show_popup(f"Error: {ex}", False)

        def open_edit_dialog(e):
            s_id = selected_student_id["value"]
            if not s_id: return
            edit_fullname_field.value = card_name.value
            edit_class_field.value = card_class.value.replace("ห้อง: ", "")
            edit_dialog.title = ft.Text("แก้ไขข้อมูลนักเรียน", weight="bold")
            edit_dialog.content = ft.Column([edit_fullname_field, edit_class_field], tight=True, spacing=10)
            edit_dialog.actions = [
                ft.TextButton("ยกเลิก", on_click=close_edit_dlg),
                ft.Button("บันทึก", bgcolor=PRIMARY, color="white", on_click=save_edit_student)
            ]
            if edit_dialog not in page.overlay: page.overlay.append(edit_dialog)
            edit_dialog.open = True
            page.update()

        del_dialog = ft.AlertDialog(modal=True)

        def close_del_dlg(e=None):
            del_dialog.open = False
            page.update()

        def confirm_delete_student(e):
            s_id = selected_student_id["value"]
            if not s_id: return
            try:
                res = requests.delete(f"{API_URL}/students/{s_id}")
                if res.status_code == 200:
                    show_popup("ลบข้อมูลนักเรียนสำเร็จ!", True)
                    close_del_dlg()
                    selected_student_id["value"] = None
                    student_card.visible = False
                    search_box.value = ""
                    fetch_students() 
                else:
                    show_popup("ลบไม่สำเร็จ (อาจมีข้อมูลอ้างอิงอยู่)", False)
            except Exception as ex:
                show_popup(f"Error: {ex}", False)

        def open_delete_dialog(e):
            s_id = selected_student_id["value"]
            if not s_id: return
            del_dialog.title = ft.Text("ยืนยันการลบ", color="red", weight="bold")
            del_dialog.content = ft.Text(f"คุณต้องการลบข้อมูลของ\n'{card_name.value}' ใช่หรือไม่?\n(การลบนี้จะไม่สามารถกู้คืนได้)")
            del_dialog.actions = [
                ft.TextButton("ยกเลิก", on_click=close_del_dlg),
                ft.Button("ลบข้อมูล", bgcolor="red", color="white", on_click=confirm_delete_student)
            ]
            if del_dialog not in page.overlay: page.overlay.append(del_dialog)
            del_dialog.open = True
            page.update()

        edit_btn = ft.IconButton(icon=ft.Icons.EDIT, icon_color=PRIMARY, tooltip="แก้ไข", on_click=open_edit_dialog)
        del_btn = ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", tooltip="ลบ", on_click=open_delete_dialog)

        student_card = ft.Card(
            content=ft.Container(
                content=ft.Row([
                    card_avatar,
                    ft.Column([card_name, card_class], spacing=5, expand=True),
                    ft.Row([edit_btn, del_btn], spacing=0) 
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=15
            ),
            width=350,
            visible=False,
            elevation=4
        )

        def fetch_students():
            nonlocal students_data
            try:
                res = requests.get(API_URL + "/students")
                if res.status_code == 200:
                    students_data = res.json()
                    unique_classes = sorted(list(set([str(s["student_class"]) for s in students_data if s.get("student_class")])))
                    classroom_dropdown.options = [ft.dropdown.Option(c) for c in unique_classes]
                    page.update()
            except Exception as ex:
                print(f"API Error fetching students: {ex}")

        def select_student(student_id, fullname, student_class):
            selected_student_id["value"] = student_id
            search_box.value = fullname
            search_results.visible = False
            safe_fullname = str(fullname).replace(" ", "%20")
            card_avatar_img.src = f"https://api.dicebear.com/9.x/bottts/png?seed={safe_fullname}"
            card_name.value = fullname
            card_class.value = f"ห้อง: {student_class}"
            student_card.visible = True
            page.update()

        def update_search(e):
            query = search_box.value.lower() if search_box.value else ""
            selected_class = classroom_dropdown.value

            if not query and not selected_class:
                selected_student_id["value"] = None
                student_card.visible = False

            filtered = students_data
            if selected_class: filtered = [s for s in filtered if s.get("student_class") == selected_class]
            if query: filtered = [s for s in filtered if query in s.get("fullname", "").lower()]

            search_results.controls.clear()
            if query or selected_class:
                for s in filtered[:5]:
                    search_results.controls.append(
                        ft.Container(
                            content=ft.ListTile(
                                title=ft.Text(s["fullname"], no_wrap=True, color="white"), 
                                on_click=lambda e, st=s: select_student(st["id"], st["fullname"], st["student_class"])
                            ),
                            width=350, bgcolor="#2c2c2c", border_radius=10, padding=0 
                        )
                    )
                search_results.visible = len(search_results.controls) > 0
            else:
                search_results.visible = False
            page.update()
                
        search_box.on_change = update_search
        classroom_dropdown.on_change = update_search

        try:
            cat_res = requests.get(API_URL + "/categories")
            if cat_res.status_code == 200: categories_data = cat_res.json()
        except: pass

        category = ft.Dropdown(
            label="3. ประเภทความดี", width=350,
            options=[ft.dropdown.Option(str(c["id"]), f"{c['activity_name']} ({c['base_point']} แต้ม)") for c in categories_data]
        )
        teacher = ft.TextField(label="4. ผู้บันทึก (ชื่อครู)", width=350)

        def save_point(e):
            if not selected_student_id["value"]:
                show_popup("กรุณาค้นหาและเลือกชื่อนักเรียนก่อนครับ", False)
                return
            if not category.value:
                show_popup("กรุณาเลือกประเภทความดีครับ", False)
                return
            try:
                res = requests.post(f"{API_URL}/add_point", json={
                    "student_id": int(selected_student_id["value"]),
                    "category_id": int(category.value),
                    "teacher": teacher.value.strip() if teacher.value else "ไม่ระบุ"
                })
                if res.status_code == 200:
                    show_popup("🎉 บันทึกคะแนนความดีสำเร็จ!", True)
                    selected_student_id["value"] = None
                    student_card.visible = False
                    search_box.value = ""
                    category.value = None
                    teacher.value = ""
                    page.update()
                else:
                    show_popup(f"บันทึกไม่สำเร็จ (รหัส: {res.status_code})", False)
            except Exception as ex:
                show_popup(f"เกิดข้อผิดพลาด: {str(ex)}", False)

        # ==========================================
        # ส่วนของการเพิ่มของรางวัล (Add Reward)
        # ==========================================
        reward_name = ft.TextField(label="ชื่อของรางวัล", width=350)
        reward_point = ft.TextField(label="คะแนนที่ใช้แลก", width=170, input_filter=ft.NumbersOnlyInputFilter())
        reward_qty = ft.TextField(label="จำนวน (ชิ้น)", width=170, input_filter=ft.NumbersOnlyInputFilter())
        reward_img = ft.TextField(label="ชื่อไฟล์รูปภาพ (เช่น รูปภาพ.jpg)", width=350)

        def save_reward(e):
            if not reward_name.value or not reward_point.value or not reward_qty.value:
                show_popup("กรุณากรอกข้อมูลของรางวัลให้ครบครับ", False)
                return
            try:
                res = requests.post(f"{API_URL}/rewards", json={
                    "name": reward_name.value,
                    "point": int(reward_point.value),
                    "quantity": int(reward_qty.value),
                    "image": reward_img.value or "default.jpg"
                })
                if res.status_code == 200:
                    show_popup("🎉 เพิ่มของรางวัลเข้าระบบสำเร็จ!", True)
                    # เคลียร์ฟอร์มหลังบันทึก
                    reward_name.value = ""
                    reward_point.value = ""
                    reward_qty.value = ""
                    reward_img.value = ""
                    page.update()
                else:
                    show_popup("เพิ่มของรางวัลไม่สำเร็จ", False)
            except Exception as ex:
                show_popup(f"Error: {ex}", False)

 
        content = ft.Column([
            ft.Text("เพิ่มคะแนนความดี", size=26, weight="bold", color=PRIMARY),
            classroom_dropdown,
            search_box,
            search_results, 
            student_card,   
            category,
            teacher,
            ft.Button("บันทึกคะแนน", bgcolor="#16a34a", color="white", width=350, height=45, on_click=save_point),
            
            ft.Divider(height=40, color="transparent"),
            ft.Divider(height=1, color="grey"),
            ft.Divider(height=10, color="transparent"),
            
            ft.Text("เพิ่มของรางวัล", size=26, weight="bold", color="#f59e0b"),
            reward_name,
            ft.Row([reward_point, reward_qty], width=350, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            reward_img,
            ft.Button("บันทึกของรางวัล", bgcolor="#f59e0b", color="white", width=350, height=45, on_click=save_reward),
            
            ft.Divider(height=50, color="transparent"), 
        ],
        alignment=ft.MainAxisAlignment.START, 
        horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        layout(
            ft.Container(content=content, padding=ft.Padding(20, 30, 20, 20)), 
            1
        )
        
        fetch_students()

    # =========================
    # REWARDS 
    # =========================
    
    def show_rewards():
        user = current_user.get("data")
        
        def on_redeem_click(e):
            if not user or user.get("username") == "guest":
                show_snackbar("บัญชี Guest ไม่สามารถแลกของรางวัลได้ ❌", False)
                return

            r_id = e.control.data["id"]
            r_name = e.control.data["name"]
            r_point = e.control.data["point"]
            
            print(f"DEBUG: กำลังกดแลก {r_name} (ID: {r_id})")

            loading_view = ft.Container(
                content=ft.Column([
                    ft.ProgressRing(width=40, height=40, color=PRIMARY),
                    ft.Text("กำลังดำเนินการ...", color=PRIMARY, weight="bold")
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="#CCFFFFFF", 
                expand=True,
                alignment=ft.Alignment(0, 0), 
            )
            
            page.overlay.append(loading_view)
            page.update()

            def process_redeem():
                try:
                    res = requests.post(f"{API_URL}/redeem", json={
                        "user_id": user['id'], 
                        "reward_id": r_id,
                        "points_required": r_point
                    }, timeout=10)
                    
                    if loading_view in page.overlay:
                        page.overlay.remove(loading_view)
                        page.update()

                    if res.status_code == 200:
                        data = res.json()
                        rem_points = data.get('remaining_points', 0)
                        
                        def close_success(ev):
                            success_dlg.open = False
                            page.update()
                            show_rewards() 

                        success_dlg = ft.AlertDialog(
                            title=ft.Text("🎉 แลกรางวัลสำเร็จ!", weight="bold"),
                            content=ft.Text(f"แลก: {r_name}\nคะแนนคงเหลือ: {rem_points} คะแนน"),
                            actions=[ft.TextButton("ตกลง", on_click=close_success)]
                        )

                        page.overlay.append(success_dlg)
                        success_dlg.open = True
                        page.update()

                    else:
                        error_detail = res.json().get('detail', 'เกิดข้อผิดพลาด')
                        
                        def close_error(ev):
                            error_dlg.open = False
                            page.update()

                        error_dlg = ft.AlertDialog(
                            title=ft.Text("❌ แลกไม่สำเร็จ!", weight="bold", color="red"),
                            content=ft.Text(f"{error_detail}"),
                            actions=[ft.TextButton("ตกลง", on_click=close_error)]
                        )
                        page.overlay.append(error_dlg)
                        error_dlg.open = True
                        page.update()

                except Exception as ex:
                    print(f"DEBUG ERROR: {ex}")
                    if loading_view in page.overlay:
                        page.overlay.remove(loading_view)
                        page.update()
                    
                    def close_network_error(ev):
                        net_error_dlg.open = False
                        page.update()

                    net_error_dlg = ft.AlertDialog(
                        title=ft.Text("❌ ผิดพลาด", weight="bold", color="red"),
                        content=ft.Text("ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้"),
                        actions=[ft.TextButton("ตกลง", on_click=close_network_error)]
                    )
                    page.overlay.append(net_error_dlg)
                    net_error_dlg.open = True
                    page.update()

            threading.Thread(target=process_redeem, daemon=True).start()

        grid = ft.GridView(expand=True, max_extent=180, child_aspect_ratio=0.6, spacing=15)

        try:
            res = requests.get(f"{API_URL}/rewards", timeout=5)
            rewards = res.json() if res.status_code == 200 else []
        except:
            rewards = []

        for r in rewards:
            rid, rname, rpoint, rimg = r.get("id"), r.get("name"), r.get("point"), r.get("image")
            
            grid.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Container(content=ft.Image(src=rimg, fit="cover"), expand=True, border_radius=10),
                        ft.Column([
                            ft.Text(rname, weight="bold", size=16, text_align="center", max_lines=1),
                            ft.Text(f"🪙 {rpoint} คะแนน", color="#f59e0b", weight="bold"),
                        ], horizontal_alignment="center", spacing=2),
                        ft.Button(
                            "แลกรางวัล",
                            color="white", bgcolor=PRIMARY, width=float('inf'),
                            data={"id": rid, "name": rname, "point": rpoint},
                            on_click=on_redeem_click 
                        )
                    ], horizontal_alignment="center", alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor="white", padding=15, border_radius=15,
                    shadow=ft.BoxShadow(blur_radius=15, color="#1A000000"), 
                )
            )

        content = ft.Column([ft.Text("แลกของรางวัล", size=22, weight="bold"), grid], expand=True)
        layout(ft.Container(content=content, padding=ft.Padding(20, 30, 20, 20)), 2)
    # ======================================================
    # RANKING 
    # ======================================================
    
    def show_leaderboard():
        try:
            res = requests.get(API_URL + "/ranking", timeout=5)
            data = res.json() if res.status_code == 200 else []
        except:
            data = []

        screen_width = min(page.width, 600) 
        scale_factor = screen_width / 600 

        p_1_w = 130 * scale_factor
        p_23_w = 100 * scale_factor
        img_1_w = 100 * scale_factor
        img_23_w = 80 * scale_factor
        text_size = max(12, 24 * scale_factor)
        
        def close_bs(bs):
            bs.open = False
            page.update()
            if bs in page.overlay:
                page.overlay.remove(bs)

        def show_top_detail(info):
            seed = info.get('top_username', 'robot')
            safe_seed = str(seed).replace(" ", "%20")
            avatar_url = f"https://api.dicebear.com/9.x/bottts/png?seed={safe_seed}"
            
            def close_bs_safe(e=None):
                try:
                    if bs in page.overlay:
                        bs.open = False
                        page.update()
                        threading.Timer(0.5, lambda: page.overlay.remove(bs) if bs in page.overlay else None).start()
                except:
                    pass

            scrollable_content = ft.Column([
                ft.Container(height=10),
                ft.Text(f"อันดับ 1 ห้อง {info.get('student_class')}", size=22, weight="bold", color=PRIMARY),
                ft.CircleAvatar(foreground_image_src=avatar_url, radius=60),
                ft.Text(info.get('top_name', 'ไม่มีข้อมูล'), size=24, weight="bold", text_align="center"),
                ft.Column([
                    ft.Text("คะแนนส่วนตัวทำไปได้", size=14, color="grey"),
                    ft.Text(f"{info.get('top_individual_score', 0)} 🪙", size=32, weight="bold", color="#f59e0b"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                ft.Container(height=20),
            ], 
            scroll="auto", 
            expand=True, 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )

            bs = ft.BottomSheet(
                ft.Container(
                    content=ft.Column([
                        scrollable_content,
                        
                        ft.Container(
                            content=ft.Button(
                                "เยี่ยมมาก!", 
                                on_click=close_bs_safe, 
                                width=220,
                                style=ft.ButtonStyle(color="white", bgcolor=PRIMARY)
                            ),
                            padding=ft.Padding.only(top=10, bottom=10),
                            alignment=ft.Alignment(0, 0)
                        ),
                    ], spacing=0),
                    
                    height=page.height * 0.7, 
                    width=min(page.width, 500),
                    padding=30, 
                    bgcolor="white", 
                    border_radius=ft.BorderRadius.only(top_left=30, top_right=30),
                ),
                open=True,
            )
            
            page.overlay.append(bs)
            page.update()

            auto_close_timer = threading.Timer(8.0, close_bs_safe)
            auto_close_timer.start()

        def create_podium_item(row_data, rank, height_base, color):
            if not row_data: 
                return ft.Container(expand=True)
            
            current_p_width = p_1_w if rank == 1 else p_23_w
            current_img_w = img_1_w if rank == 1 else img_23_w
            current_height = height_base * scale_factor 

            return ft.Column([
                ft.Container(
                    content=ft.Image(
                        src=row_data.get("room_image", ""), 
                        fit="cover", 
                    ),
                    width=current_img_w, 
                    height=current_img_w * 0.7,
                    bgcolor="white", 
                    border_radius=10,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS, 
                    shadow=ft.BoxShadow(blur_radius=8, color="#30000000"),
                    on_click=lambda e: show_top_detail(row_data)
                ),
                
                ft.Text(f"🪙{row_data.get('total_class_point', 0)}", size=max(12, 16 * scale_factor), color=PRIMARY, weight="bold"),
                
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.WORKSPACE_PREMIUM, color="white", size=20 * scale_factor) if rank == 1 else ft.Container(),
                        ft.Text(str(rank), size=text_size, weight="bold", color="white"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                    bgcolor=color,
                    width=current_p_width,
                    height=current_height,
                    border_radius=ft.BorderRadius.only(top_left=15, top_right=15),
                    alignment=ft.Alignment(0, 0),
                    on_click=lambda e: show_top_detail(row_data)
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5, alignment=ft.MainAxisAlignment.END)

        top_1 = data[0] if len(data) > 0 else None
        top_2 = data[1] if len(data) > 1 else None
        top_3 = data[2] if len(data) > 2 else None
        others = data[3:] if len(data) > 3 else []

        podium_section = ft.Container(
            content=ft.Row([
                create_podium_item(top_2, 2, 100, ft.Colors.BLUE_GREY_300),  
                create_podium_item(top_1, 1, 160, ft.Colors.AMBER_400),    
                create_podium_item(top_3, 3, 75, ft.Colors.BROWN_400),     
            ], 
            alignment=ft.MainAxisAlignment.CENTER, 
            vertical_alignment=ft.CrossAxisAlignment.END, 
            spacing=page.width * 0.01 
            ),
            padding=ft.Padding.only(top=10, bottom=10)
        )

        others_list = ft.ListView(expand=True, spacing=10)
        for i, row in enumerate(others):
            others_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(f"{i+4}", size=16, weight="bold", color="grey", width=30),
                        ft.Container(
                            content=ft.Image(src=row.get("room_image", ""), fit="cover"),
                            width=55, height=45, border_radius=8,
                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS 
                        ),
                        ft.Column([
                            ft.Text(f"ห้อง {row.get('student_class', '')}", weight="bold", color="#1e293b", size=14),
                            ft.Text(f"{row.get('total_class_point', 0)} 🪙", size=12, color=PRIMARY),
                        ], expand=True, spacing=0),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, color="grey-300")
                    ]),
                    padding=12, bgcolor="white", border_radius=12,
                    shadow=ft.BoxShadow(blur_radius=5, color="#0A000000"),
                    on_click=lambda e, r=row: show_top_detail(r)
                )
            )
        
        main_layout = ft.Container(
            content=ft.Column([
                ft.Text("อันดับความดีรายห้อง", size=26, weight="bold", color=PRIMARY),
                podium_section,
                ft.Divider(height=20, color="transparent"),
                others_list
            ], expand=True),
            width=min(page.width * 0.95, 800),
            expand=True,
            padding=ft.Padding(10, 40, 10, 20)        )

        layout(ft.Row([main_layout], alignment=ft.MainAxisAlignment.CENTER, expand=True), 3)

    # =========================
    # PROFILE 
    # =========================
        
    def show_profile(target_user=None):
        
        is_viewing_other = target_user is not None
        user = target_user if is_viewing_other else current_user["data"]
        
        total_point = 0
        history_data = []
        try:
            res = requests.get(f"{API_URL}/user_points/{user['id']}", timeout=5)
            if res.status_code == 200:
                history_data = res.json()
                total_point = sum(item['point'] for item in history_data)
                
                if not is_viewing_other:
                    current_user["data"]["total_point"] = total_point
            else:
                total_point = user.get("total_point", 0)
        except:
            total_point = user.get("total_point", 0)

        redeem_history_data = []
        try:
            res_redeem = requests.get(f"{API_URL}/user_redeem_history/{user['id']}", timeout=5)
            if res_redeem.status_code == 200:
                redeem_history_data = res_redeem.json()
        except:
            pass

        is_dark = page.theme_mode == ft.ThemeMode.DARK
        text_col = "white" if is_dark else "black"
        label_col = "white70" if is_dark else "#9e9e9e"
        card_bg = "surfaceVariant" if is_dark else "white"
        list_item_bg = "surfaceVariant" if is_dark else "#f1f5f9"
        
        safe_username = str(user.get('username', user.get('fullname', 'guest'))).replace(" ", "%20")
        avatar_url = f"https://api.dicebear.com/9.x/bottts/png?seed={safe_username}"

        def get_emoji(desc):
            desc = desc or ""
            if any(w in desc for w in ["ขยะ", "ทำความสะอาด", "กวาด"]): return "🧹"
            elif any(w in desc for w in ["เพื่อน", "ติว", "แบ่งปัน"]): return "🤝"
            else: return "⭐"

        def get_badge(pts):
            if pts >= 500: return "🥇 ระดับทอง"
            elif pts >= 200: return "🥈 ระดับเงิน"
            else: return "🌱 มือใหม่"

        top_nav = ft.Row([
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK_IOS_NEW, 
                icon_color=PRIMARY,
                on_click=lambda _: show_admin_dashboard()
            ) 
        ], alignment=ft.MainAxisAlignment.START) if is_viewing_other else ft.Container()


        positive_history = [item for item in history_data if item.get('point', 0) > 0]
        
        recent_controls = []
        if not positive_history:
            recent_controls.append(ft.Text("ยังไม่มีประวัติการทำความดี ", color=label_col, italic=True, size=13))
        else:
            for item in positive_history[:5]:
                recent_controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(get_emoji(item.get("description", "")), size=16),
                            ft.Text(item.get("description", "-"), size=12, expand=True, no_wrap=True, color=text_col), 
                            ft.Text(f"+{item['point']} แต้ม", color="#16a34a", weight="bold", size=12),
                        ], spacing=8),
                        padding=10, bgcolor=list_item_bg, border_radius=9,
                    )
                )

        redeem_controls = []
        if not redeem_history_data:
            redeem_controls.append(ft.Text("ยังไม่มีประวัติการแลกรางวัล", color=label_col, italic=True, size=13))
        else:
            for item in redeem_history_data[:5]:
                redeem_controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Image(src=item["image"], width=40, height=40, border_radius=5, fit="cover"),
                            ft.Column([
                                ft.Text(item["name"], size=13, weight="bold", color=text_col),
                                ft.Text(item.get("date", "-"), size=11, color=label_col),
                            ], spacing=1, expand=True),
                            ft.Text(f"-{item['point']} แต้ม", color="#ef4444", weight="bold", size=12),
                        ], spacing=10),
                        padding=10, bgcolor=list_item_bg, border_radius=9,
                    )
                )

        content_list = [
            top_nav,
            ft.CircleAvatar(foreground_image_src=avatar_url, radius=55),
            ft.Text(user["fullname"], size=22, weight="bold", color=text_col),
            ft.Text(f"@{user.get('username', 'student')} | ห้อง {user.get('student_class', '-')}", size=14, color=label_col),
            ft.Text(get_badge(total_point), size=13, color=PRIMARY),

            ft.Divider(height=8, color="transparent"),

            ft.Container(
                content=ft.Row([
                    ft.Text("⭐", size=22),
                    ft.Text(f"{total_point} แต้ม", size=22, weight="bold", color=PRIMARY),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                padding=15,
                bgcolor="#ede9fe" if not is_dark else ft.Colors.with_opacity(0.1, PRIMARY),
                border_radius=14, width=260,
            ),

            ft.Divider(height=8, color="transparent"),

            ft.Container(
                content=ft.Column([
                    ft.Row([ft.Text("📋 ประวัติการทำความดีล่าสุด", weight="bold", size=14, color=text_col)]),
                    ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                    *recent_controls,  
                ], spacing=7),
                bgcolor=card_bg, padding=14, border_radius=14, width=340,
                shadow=ft.BoxShadow(blur_radius=5, color="#0A000000") if not is_dark else None,
            ),

            ft.Divider(height=4, color="transparent"),

            ft.Container(
                content=ft.Column([
                    ft.Row([ft.Text("🎁 ประวัติการแลกรางวัล", weight="bold", size=14, color=text_col)]),
                    ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                    *redeem_controls,  
                ], spacing=7),
                bgcolor=card_bg, padding=14, border_radius=14, width=340,
                shadow=ft.BoxShadow(blur_radius=5, color="#0A000000") if not is_dark else None,
            ),
        ]

        if not is_viewing_other:
            content_list.extend([
                ft.Divider(height=8, color="transparent"),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("🌙 Dark Mode", size=13, weight="w500", color=text_col),
                            ft.Switch(value=is_dark, active_color=PRIMARY, on_change=toggle_dark),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                        ft.TextButton(
                            content=ft.Text("ออกจากระบบ", color=ft.Colors.RED_600, weight="w500"),
                            icon=ft.Icons.LOGOUT,
                            icon_color=ft.Colors.RED_600,
                            on_click=lambda _: show_login()
                        ),
                    ], spacing=4),
                    bgcolor=card_bg, padding=14, border_radius=14, width=340,
                    shadow=ft.BoxShadow(blur_radius=5, color="#0A000000") if not is_dark else None,
                ),
                ft.Container(height=16),
            ])

        content = ft.Column(
            controls=content_list,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True, scroll=ft.ScrollMode.AUTO, spacing=8,
        )

        active_nav_index = 0 if is_viewing_other else 4

        layout(
            ft.Container(
                content=content, 
                padding=ft.Padding(20, 20 if is_viewing_other else 40, 20, 20) 
            ), 
            active_nav_index
        )

    show_login()
ft.run(main)