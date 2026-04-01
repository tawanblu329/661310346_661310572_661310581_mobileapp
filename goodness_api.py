from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
from typing import Optional
from datetime import datetime
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory="rewards"), name="images")
app.mount("/room_images", StaticFiles(directory="classrooms"), name="room_images")

# =========================
# Database Config
# =========================
db_config = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "goodness_app"
}

@app.get("/test-db")
def test_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1")

    cursor.close()
    conn.close()

    return {"status": "connected"}

@app.get("/") 
def root():
    return {"message": "Goodness API is running"}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        print("✅ DB CONNECTED")
        return connection
    except Error as e:
        print("❌ DB ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# Models
# =========================
class LoginRequest(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: Optional[int] = None
    username: str
    password: str
    fullname: str
    role: str
    student_class: str

class Point(BaseModel):
    user_id: int
    point: int
    description: str

class Reward(BaseModel):
    name: str
    point: int
    quantity: int
    image: str

class AddPoint(BaseModel):
    student_id: int
    category_id: int
    teacher: str

class RedeemRequest(BaseModel):
    user_id: int
    reward_id: int
    points_required: int

# =========================
# ADMIN DASHBOARD API
# =========================
@app.get("/recent_points")
def get_recent_points():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT p.point, p.description, DATE_FORMAT(p.created_at, '%d/%m/%Y %H:%i') as date,
               u.fullname, u.student_class
        FROM points p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC
        LIMIT 20
    """
    cursor.execute(query)
    data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return data
    

# =========================
# Login
# =========================

@app.post("/login")
def login(data: LoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT id, username, fullname, role, student_class FROM users WHERE username=%s AND password=%s"
    
    cursor.execute(query, (data.username, data.password))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid login")
    
    user["total_point"] = 0 
    return {"user": user}

# =========================
# USERS CRUD
# =========================

@app.get("/users")
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

@app.post("/users")
def add_user(user: User):
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO users (username,password,fullname,role,student_class)
    VALUES (%s,%s,%s,%s,%s)
    """
    cursor.execute(sql,(user.username,user.password,user.fullname,user.role,user.student_class))
    conn.commit()

    cursor.close()
    conn.close()
    return {"message":"User added"}

class UpdateStudent(BaseModel):
    fullname: str
    student_class: str

@app.get("/students/{student_id}")
def get_student_by_id(student_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, fullname, student_class FROM users WHERE id = %s AND role = 'student'", (student_id,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.put("/students/{student_id}")
def update_student(student_id: int, data: UpdateStudent):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE id = %s AND role = 'student'", (student_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Student not found")

        
        sql = "UPDATE users SET fullname = %s, student_class = %s WHERE id = %s AND role = 'student'"
        cursor.execute(sql, (data.fullname, data.student_class, student_id))
        conn.commit()
        return {"message": "Student updated successfully"}
    except Exception as e:
        conn.rollback()
        print("❌ DB UPDATE ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = %s AND role = 'student'", (student_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Student not found")
            
        return {"message": "Student deleted successfully"}
    except Exception as e:
        conn.rollback()
        print("❌ DB DELETE ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
        
# =========================
# POINTS CRUD
# =========================
    
@app.post("/add_point")
def add_point(data: AddPoint):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT activity_name, base_point 
            FROM categories 
            WHERE id = %s
        """, (data.category_id,))
        cat = cursor.fetchone()

        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")

        point = cat["base_point"]
        
        desc = f"{cat['activity_name']} (บันทึกโดย: {data.teacher})"
        now = datetime.now()

        cursor.execute("""
            INSERT INTO points (user_id, category_id, point, description, created_at, image)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (data.student_id, data.category_id, point, desc, now, ""))

        conn.commit()
        return {"message": "Point added successfully"}
        
    except Exception as e:
        print("❌ ERROR in add_point:", e) 
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# =========================
# GET USER POINT HISTORY
# =========================
@app.get("/user_points/{user_id}")
def get_user_points(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT point, description, DATE_FORMAT(created_at, '%d/%m/%Y %H:%i') as date
        FROM points
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))
    
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

# =========================
# REWARDS CRUD แก้
# =========================
@app.get("/rewards")
def get_rewards():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM rewards")
    data = cursor.fetchall()
    cursor.close()
    conn.close()


    base_url = "http://172.30.123.207:8000/images"
    
    for row in data:
        if row.get("image"):
            row["image"] = f"{base_url}/{row['image']}"
            
    return data 

@app.post("/rewards")
def add_reward(reward: Reward):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO rewards (name, point, quantity, image) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (reward.name, reward.point, reward.quantity, reward.image))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Reward added successfully"}

@app.get("/students")
def get_students():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, fullname, student_class
        FROM users
        WHERE role = 'student'
        ORDER BY student_class, fullname
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

@app.get("/categories")
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, activity_name, base_point, group_name
        FROM categories
        WHERE is_active = 1
        ORDER BY group_name, activity_name
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

# =========================
# REDEEM (รวมให้เหลืออันเดียวที่สมบูรณ์)
# =========================

class RedeemRequest(BaseModel):
    user_id: int
    reward_id: int
    points_required: int

@app.post("/redeem")
def redeem_reward(req: RedeemRequest):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT IFNULL(SUM(point), 0) as total FROM points WHERE user_id = %s", (req.user_id,))
        result = cursor.fetchone()
        current_points = result['total']
        
        cursor.execute("SELECT name, point FROM rewards WHERE id = %s", (req.reward_id,))
        reward = cursor.fetchone()

        if not reward:
            raise HTTPException(status_code=404, detail="ไม่พบของรางวัล")

        if current_points < req.points_required:
            raise HTTPException(status_code=400, detail=f"คะแนนไม่พอ (มี {current_points} ต้องการ {req.points_required})")

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        query_points = "INSERT INTO points (user_id, point, description, created_at, image) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query_points, (
            req.user_id, 
            -req.points_required, 
            f"แลกรางวัล: {reward['name']}", 
            now,
            ""
        ))
        
        query_redeem = "INSERT INTO redeem (user_id, reward_id, created_at) VALUES (%s, %s, %s)"
        cursor.execute(query_redeem, (req.user_id, req.reward_id, now))

        conn.commit()
        return {
            "status": "success", 
            "message": "Redeemed successfully",
            "remaining_points": current_points - req.points_required
        }
    
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# =========================
# GET USER REDEEM HISTORY
# =========================
@app.get("/user_redeem_history/{user_id}")
def get_user_redeem_history(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT r.name, r.point, r.image, DATE_FORMAT(rd.created_at, '%d/%m/%Y %H:%i') as date
        FROM redeem rd
        JOIN rewards r ON rd.reward_id = r.id
        WHERE rd.user_id = %s
        ORDER BY rd.created_at DESC
    """, (user_id,))
    
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    base_url = "http://172.30.123.207:8000/images"
    
    for row in data:
        if row.get("image"):
            row["image"] = f"{base_url}/{row['image']}"
            
    return data

# =========================
# RANKING CLASS (แก้)
# =========================
@app.get("/ranking")
def ranking():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT 
        u.student_class,
        c.room_image,
        SUM(p.point) as total_class_point, 
        (SELECT u2.fullname FROM users u2 
         JOIN points p2 ON u2.id = p2.user_id 
         WHERE u2.student_class = u.student_class 
         GROUP BY u2.id ORDER BY SUM(p2.point) DESC LIMIT 1) as top_name,
        (SELECT u2.username FROM users u2 
         JOIN points p2 ON u2.id = p2.user_id 
         WHERE u2.student_class = u.student_class 
         GROUP BY u2.id ORDER BY SUM(p2.point) DESC LIMIT 1) as top_username,
        (SELECT SUM(p2.point) FROM users u2 
         JOIN points p2 ON u2.id = p2.user_id 
         WHERE u2.student_class = u.student_class 
         GROUP BY u2.id ORDER BY SUM(p2.point) DESC LIMIT 1) as top_individual_score
    FROM users u
    JOIN points p ON u.id = p.user_id
    LEFT JOIN classrooms c ON u.student_class = c.class_name
    WHERE u.role = 'student'
    GROUP BY u.student_class
    ORDER BY total_class_point DESC
    """
    cursor.execute(query)
    data = cursor.fetchall()

    base_url = "http://172.30.123.207:8000"    

    for row in data:
        if row["room_image"]:
            row["room_image"] = f"{base_url}/room_images/{row['room_image']}"
        else:
            row["room_image"] = "https://via.placeholder.com/150"

    cursor.close()
    conn.close()
    return data

