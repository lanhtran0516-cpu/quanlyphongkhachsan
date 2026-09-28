import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
from pathlib import Path
import hashlib

# ============================================================
# CẤU HÌNH APP
# ============================================================

st.set_page_config(
    page_title="Hotel PMS",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = Path("hotel_pms.db")


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def execute(query, params=(), fetch=False):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)

    if fetch:
        result = cursor.fetchall()
        conn.close()
        return result

    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def read_df(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_database():

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # ROOMS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            room_type TEXT NOT NULL,
            floor INTEGER NOT NULL,
            price REAL NOT NULL,
            capacity INTEGER DEFAULT 2,
            status TEXT DEFAULT 'Trống',
            note TEXT DEFAULT ''
        )
    """)

    # --------------------------------------------------------
    # GUESTS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            id_number TEXT,
            address TEXT,
            created_at TEXT
        )
    """)

    # --------------------------------------------------------
    # BOOKINGS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_code TEXT UNIQUE NOT NULL,
            guest_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL,
            adults INTEGER DEFAULT 1,
            children INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Đã đặt',
            room_charge REAL DEFAULT 0,
            deposit REAL DEFAULT 0,
            note TEXT DEFAULT '',
            created_at TEXT
        )
    """)

    # --------------------------------------------------------
    # HOUSEKEEPING
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS housekeeping (
            room_id INTEGER PRIMARY KEY,
            cleaning_status TEXT DEFAULT 'Sạch',
            last_cleaned TEXT,
            note TEXT DEFAULT ''
        )
    """)

    # --------------------------------------------------------
    # SERVICES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            service_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            unit_price REAL DEFAULT 0,
            amount REAL DEFAULT 0,
            created_at TEXT
        )
    """)

    # --------------------------------------------------------
    # INVOICES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            booking_id INTEGER NOT NULL,
            room_charge REAL DEFAULT 0,
            service_charge REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            total REAL DEFAULT 0,
            payment_method TEXT,
            payment_status TEXT DEFAULT 'Chưa thanh toán',
            created_at TEXT
        )
    """)

    # --------------------------------------------------------
    # TÀI KHOẢN MẪU
    # --------------------------------------------------------

    user_count = cursor.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    if user_count == 0:

        users = [
            (
                "admin",
                hash_password("123456"),
                "Quản lý khách sạn",
                "Quản lý"
            ),
            (
                "reception",
                hash_password("123456"),
                "Nhân viên lễ tân",
                "Lễ tân"
            ),
            (
                "housekeeping",
                hash_password("123456"),
                "Nhân viên buồng phòng",
                "Housekeeping"
            )
        ]

        cursor.executemany("""
            INSERT INTO users
            (username, password, full_name, role)
            VALUES (?, ?, ?, ?)
        """, users)

    # --------------------------------------------------------
    # PHÒNG MẪU
    # --------------------------------------------------------

    room_count = cursor.execute(
        "SELECT COUNT(*) FROM rooms"
    ).fetchone()[0]

    if room_count == 0:

        rooms = [

            ("101", "Standard", 1, 800000, 2, "Trống", ""),
            ("102", "Standard", 1, 800000, 2, "Đang ở", ""),
            ("103", "Deluxe", 1, 1200000, 2, "Đã đặt", ""),
            ("104", "Deluxe", 1, 1200000, 2, "Đang dọn", ""),

            ("201", "Standard", 2, 800000, 2, "Trống", ""),
            ("202", "Superior", 2, 1000000, 2, "Bảo trì", "Kiểm tra điều hòa"),
            ("203", "Deluxe", 2, 1200000, 2, "Trống", ""),
            ("204", "Suite", 2, 2000000, 4, "Đang ở", ""),

            ("301", "Superior", 3, 1000000, 2, "Trống", ""),
            ("302", "Deluxe", 3, 1200000, 2, "Trống", ""),
            ("303", "Suite", 3, 2000000, 4, "Trống", ""),
            ("304", "Suite", 3, 2000000, 4, "Đang dọn", "")
        ]

        cursor.executemany("""
            INSERT INTO rooms
            (
                room_number,
                room_type,
                floor,
                price,
                capacity,
                status,
                note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, rooms)

    # --------------------------------------------------------
    # HOUSEKEEPING MẶC ĐỊNH
    # --------------------------------------------------------

    room_ids = cursor.execute(
        "SELECT id FROM rooms"
    ).fetchall()

    for room in room_ids:

        cursor.execute("""
            INSERT OR IGNORE INTO housekeeping
            (
                room_id,
                cleaning_status,
                last_cleaned
            )
            VALUES (?, ?, ?)
        """, (
            room["id"],
            "Sạch",
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ))

    # --------------------------------------------------------
    # KHÁCH MẪU
    # --------------------------------------------------------

    guest_count = cursor.execute(
        "SELECT COUNT(*) FROM guests"
    ).fetchone()[0]

    if guest_count == 0:

        cursor.execute("""
            INSERT INTO guests
            (
                full_name,
                phone,
                email,
                id_number,
                address,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "Nguyễn Văn An",
            "0901234567",
            "an@gmail.com",
            "079123456789",
            "TP. Hồ Chí Minh",
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()


init_database()


# ============================================================
# HÀM TIỆN ÍCH
# ============================================================

def money(value):
    return f"{float(value):,.0f} đ".replace(",", ".")


def calculate_nights(check_in, check_out):

    if isinstance(check_in, str):
        check_in = date.fromisoformat(check_in)

    if isinstance(check_out, str):
        check_out = date.fromisoformat(check_out)

    return max((check_out - check_in).days, 0)


def create_booking_code():
    return "BK" + datetime.now().strftime("%Y%m%d%H%M%S%f")[:17]


def create_invoice_number():
    return "HD" + datetime.now().strftime("%Y%m%d%H%M%S%f")[:17]


def status_icon(status):

    icons = {
        "Trống": "🟢",
        "Đã đặt": "🟡",
        "Đang ở": "🔵",
        "Đang dọn": "🟠",
        "Bảo trì": "🔴"
    }

    return icons.get(status, "⚪")


def login_user(username, password):

    password_hash = hash_password(password)

    users = execute("""
        SELECT *
        FROM users
        WHERE username = ?
        AND password = ?
    """, (username, password_hash), fetch=True)

    if users:
        return dict(users[0])

    return None


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.main-title {
    font-size: 32px;
    font-weight: 700;
}

.sub-title {
    color: #6b7280;
    margin-bottom: 20px;
}

.room-card {
    border: 1px solid #e5e7eb;
    border-radius: 15px;
    padding: 16px;
    margin-bottom: 12px;
    background: white;
}

.room-number {
    font-size: 21px;
    font-weight: 700;
}

.room-price {
    font-weight: 600;
}

.small-text {
    color: #6b7280;
    font-size: 13px;
}

.login-container {
    max-width: 450px;
    margin: 80px auto;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# LOGIN
# ============================================================

if "user" not in st.session_state:
    st.session_state.user = None


if st.session_state.user is None:

    st.markdown(
        "<div class='login-container'>",
        unsafe_allow_html=True
    )

    st.title("🏨 Hotel PMS")

    st.caption(
        "Hệ thống quản lý phòng và vận hành khách sạn"
    )

    with st.form("login_form"):

        username = st.text_input(
            "Tên đăng nhập"
        )

        password = st.text_input(
            "Mật khẩu",
            type="password"
        )

        submit = st.form_submit_button(
            "🔐 Đăng nhập",
            type="primary",
            use_container_width=True
        )

        if submit:

            user = login_user(
                username,
                password
            )

            if user:

                st.session_state.user = user

                st.rerun()

            else:

                st.error(
                    "Tên đăng nhập hoặc mật khẩu không đúng."
                )

    st.info("""
**Tài khoản demo**

Quản lý: `admin` / `123456`

Lễ tân: `reception` / `123456`

Housekeeping: `housekeeping` / `123456`
""")

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    st.stop()


# ============================================================
# THÔNG TIN USER
# ============================================================

user = st.session_state.user

role = user["role"]


# ============================================================
# SIDEBAR MENU
# ============================================================

st.sidebar.title("🏨 HOTEL PMS")

st.sidebar.success(
    f"👤 {user['full_name']}\n\n"
    f"Vai trò: {role}"
)


all_menus = [
    "📊 Dashboard",
    "🛏️ Sơ đồ phòng",
    "📅 Đặt phòng",
    "👤 Khách hàng",
    "🧾 Check-in / Check-out",
    "🧹 Housekeeping",
    "💳 Hóa đơn",
    "📈 Báo cáo",
    "⚙️ Quản lý phòng"
]


if role == "Housekeeping":

    menus = [
        "🛏️ Sơ đồ phòng",
        "🧹 Housekeeping"
    ]

elif role == "Lễ tân":

    menus = [
        "📊 Dashboard",
        "🛏️ Sơ đồ phòng",
        "📅 Đặt phòng",
        "👤 Khách hàng",
        "🧾 Check-in / Check-out",
        "💳 Hóa đơn"
    ]

else:

    menus = all_menus


page = st.sidebar.radio(
    "MENU",
    menus
)


if st.sidebar.button(
    "🚪 Đăng xuất",
    use_container_width=True
):

    st.session_state.user = None

    st.rerun()


st.sidebar.divider()

st.sidebar.caption(
    "Hotel PMS • Streamlit + SQLite"
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "📊 Dashboard":

    st.markdown(
        '<div class="main-title">📊 Dashboard</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">'
        'Tổng quan hoạt động khách sạn'
        '</div>',
        unsafe_allow_html=True
    )

    rooms = read_df(
        "SELECT * FROM rooms"
    )

    bookings = read_df(
        "SELECT * FROM bookings"
    )

    total_rooms = len(rooms)

    available_rooms = len(
        rooms[rooms["status"] == "Trống"]
    )

    occupied_rooms = len(
        rooms[rooms["status"] == "Đang ở"]
    )

    reserved_rooms = len(
        rooms[rooms["status"] == "Đã đặt"]
    )

    cleaning_rooms = len(
        rooms[rooms["status"] == "Đang dọn"]
    )

    maintenance_rooms = len(
        rooms[rooms["status"] == "Bảo trì"]
    )

    occupancy = 0

    if total_rooms > 0:

        occupancy = (
            occupied_rooms / total_rooms
        ) * 100

    revenue = 0

    if not bookings.empty:

        revenue = bookings[
            bookings["status"].isin(
                ["Đang ở", "Đã trả"]
            )
        ]["room_charge"].sum()

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric(
        "Tổng phòng",
        total_rooms
    )

    c2.metric(
        "🟢 Phòng trống",
        available_rooms
    )

    c3.metric(
        "🔵 Đang ở",
        occupied_rooms
    )

    c4.metric(
        "🟡 Đã đặt",
        reserved_rooms
    )

    c5.metric(
        "🧹 Đang dọn",
        cleaning_rooms
    )

    c6.metric(
        "Công suất",
        f"{occupancy:.1f}%"
    )

    st.divider()

    # --------------------------------------------------------
    # BIỂU ĐỒ
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.subheader(
            "🏨 Tình trạng phòng"
        )

        room_chart = pd.DataFrame({
            "Trạng thái": [
                "Trống",
                "Đã đặt",
                "Đang ở",
                "Đang dọn",
                "Bảo trì"
            ],
            "Số phòng": [
                available_rooms,
                reserved_rooms,
                occupied_rooms,
                cleaning_rooms,
                maintenance_rooms
            ]
        })

        st.bar_chart(
            room_chart.set_index(
                "Trạng thái"
            )
        )

    with col2:

        st.subheader(
            "💰 Doanh thu"
        )

        st.metric(
            "Doanh thu tiền phòng",
            money(revenue)
        )

        st.metric(
            "Phòng bảo trì",
            maintenance_rooms
        )

    # --------------------------------------------------------
    # BOOKING GẦN ĐÂY
    # --------------------------------------------------------

    st.subheader(
        "📅 Booking gần đây"
    )

    recent = read_df("""
        SELECT
            b.booking_code,
            g.full_name,
            r.room_number,
            b.check_in,
            b.check_out,
            b.status,
            b.room_charge
        FROM bookings b
        JOIN guests g
            ON g.id = b.guest_id
        JOIN rooms r
            ON r.id = b.room_id
        ORDER BY b.id DESC
        LIMIT 10
    """)

    if recent.empty:

        st.info(
            "Chưa có dữ liệu booking."
        )

    else:

        st.dataframe(
            recent.rename(columns={
                "booking_code": "Mã booking",
                "full_name": "Khách hàng",
                "room_number": "Phòng",
                "check_in": "Check-in",
                "check_out": "Check-out",
                "status": "Trạng thái",
                "room_charge": "Tiền phòng"
            }),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# SƠ ĐỒ PHÒNG
# ============================================================

elif page == "🛏️ Sơ đồ phòng":

    st.title(
        "🛏️ Sơ đồ phòng khách sạn"
    )

    rooms = read_df("""
        SELECT *
        FROM rooms
        ORDER BY floor, room_number
    """)

    col1, col2 = st.columns(2)

    floors = ["Tất cả"] + sorted(
        rooms["floor"].unique().tolist()
    )

    floor_filter = col1.selectbox(
        "Tầng",
        floors
    )

    status_filter = col2.selectbox(
        "Trạng thái",
        [
            "Tất cả",
            "Trống",
            "Đã đặt",
            "Đang ở",
            "Đang dọn",
            "Bảo trì"
        ]
    )

    filtered = rooms.copy()

    if floor_filter != "Tất cả":

        filtered = filtered[
            filtered["floor"] == floor_filter
        ]

    if status_filter != "Tất cả":

        filtered = filtered[
            filtered["status"] == status_filter
        ]

    st.caption(
        "🟢 Trống  |  🟡 Đã đặt  |  "
        "🔵 Đang ở  |  🟠 Đang dọn  |  🔴 Bảo trì"
    )

    cols = st.columns(4)

    for index, room in filtered.iterrows():

        with cols[index % 4]:

            st.markdown(
                f"""
                <div class="room-card">

                <div class="room-number">
                {status_icon(room['status'])}
                Phòng {room['room_number']}
                </div>

                <b>{room['room_type']}</b>
                · Tầng {room['floor']}

                <br>

                <span class="small-text">
                Sức chứa: {room['capacity']} khách
                </span>

                <br>

                <b>{room['status']}</b>

                <br>

                <span class="room-price">
                {money(room['price'])}/đêm
                </span>

                <br>

                <span class="small-text">
                {room['note'] or ''}
                </span>

                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# ĐẶT PHÒNG
# ============================================================

elif page == "📅 Đặt phòng":

    st.title(
        "📅 Quản lý đặt phòng"
    )

    tab1, tab2 = st.tabs([
        "📋 Danh sách booking",
        "➕ Tạo booking"
    ])

    # --------------------------------------------------------
    # DANH SÁCH
    # --------------------------------------------------------

    with tab1:

        bookings = read_df("""
            SELECT
                b.booking_code,
                g.full_name,
                g.phone,
                r.room_number,
                r.room_type,
                b.check_in,
                b.check_out,
                b.adults,
                b.children,
                b.status,
                b.room_charge,
                b.deposit,
                b.note
            FROM bookings b
            JOIN guests g
                ON g.id = b.guest_id
            JOIN rooms r
                ON r.id = b.room_id
            ORDER BY b.id DESC
        """)

        if bookings.empty:

            st.info(
                "Chưa có booking."
            )

        else:

            st.dataframe(
                bookings.rename(columns={
                    "booking_code": "Mã",
                    "full_name": "Khách",
                    "phone": "SĐT",
                    "room_number": "Phòng",
                    "room_type": "Loại",
                    "check_in": "Check-in",
                    "check_out": "Check-out",
                    "adults": "Người lớn",
                    "children": "Trẻ em",
                    "status": "Trạng thái",
                    "room_charge": "Tiền phòng",
                    "deposit": "Đặt cọc",
                    "note": "Ghi chú"
                }),
                use_container_width=True,
                hide_index=True
            )

    # --------------------------------------------------------
    # TẠO BOOKING
    # --------------------------------------------------------

    with tab2:

        guests = read_df("""
            SELECT *
            FROM guests
            ORDER BY full_name
        """)

        rooms = read_df("""
            SELECT *
            FROM rooms
            WHERE status = 'Trống'
            ORDER BY room_number
        """)

        if guests.empty:

            st.warning(
                "Chưa có khách hàng."
            )

        elif rooms.empty:

            st.warning(
                "Hiện không có phòng trống."
            )

        else:

            with st.form(
                "create_booking"
            ):

                guest_map = {
                    f"{row.full_name} - {row.phone or ''}":
                    int(row.id)
                    for _, row in guests.iterrows()
                }

                room_map = {
                    f"Phòng {row.room_number} - "
                    f"{row.room_type} - "
                    f"{money(row.price)}":
                    int(row.id)
                    for _, row in rooms.iterrows()
                }

                guest_choice = st.selectbox(
                    "👤 Khách hàng",
                    list(guest_map.keys())
                )

                room_choice = st.selectbox(
                    "🛏️ Phòng",
                    list(room_map.keys())
                )

                col1, col2 = st.columns(2)

                check_in = col1.date_input(
                    "Ngày check-in",
                    date.today()
                )

                check_out = col2.date_input(
                    "Ngày check-out",
                    date.today()
                )

                col1, col2, col3 = st.columns(3)

                adults = col1.number_input(
                    "Người lớn",
                    min_value=1,
                    max_value=20,
                    value=1
                )

                children = col2.number_input(
                    "Trẻ em",
                    min_value=0,
                    max_value=20,
                    value=0
                )

                deposit = col3.number_input(
                    "Tiền đặt cọc",
                    min_value=0,
                    max_value=100000000,
                    value=0,
                    step=100000
                )

                note = st.text_area(
                    "Ghi chú"
                )

                submit = st.form_submit_button(
                    "📅 Tạo booking",
                    type="primary"
                )

                if submit:

                    if check_out <= check_in:

                        st.error(
                            "Ngày check-out phải sau ngày check-in."
                        )

                    else:

                        guest_id = guest_map[
                            guest_choice
                        ]

                        room_id = room_map[
                            room_choice
                        ]

                        room = rooms[
                            rooms["id"] == room_id
                        ].iloc[0]

                        number_of_nights = calculate_nights(
                            check_in,
                            check_out
                        )

                        room_charge = (
                            number_of_nights
                            * float(room["price"])
                        )

                        code = create_booking_code()

                        execute("""
                            INSERT INTO bookings
                            (
                                booking_code,
                                guest_id,
                                room_id,
                                check_in,
                                check_out,
                                adults,
                                children,
                                status,
                                room_charge,
                                deposit,
                                note,
                                created_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            code,
                            guest_id,
                            room_id,
                            check_in.isoformat(),
                            check_out.isoformat(),
                            adults,
                            children,
                            "Đã đặt",
                            room_charge,
                            deposit,
                            note,
                            datetime.now().isoformat()
                        ))

                        execute("""
                            UPDATE rooms
                            SET status = 'Đã đặt'
                            WHERE id = ?
                        """, (room_id,))

                        st.success(
                            f"Đặt phòng thành công — "
                            f"{code} — "
                            f"{money(room_charge)}"
                        )

                        st.rerun()


# ============================================================
# KHÁCH HÀNG
# ============================================================

elif page == "👤 Khách hàng":

    st.title(
        "👤 Quản lý khách hàng"
    )

    tab1, tab2 = st.tabs([
        "📋 Danh sách khách",
        "➕ Thêm khách"
    ])

    with tab1:

        guests = read_df("""
            SELECT *
            FROM guests
            ORDER BY id DESC
        """)

        search = st.text_input(
            "🔎 Tìm khách hàng",
            placeholder="Tên, SĐT hoặc CCCD..."
        )

        if search:

            mask = (
                guests["full_name"]
                .fillna("")
                .str.contains(search, case=False)
                |
                guests["phone"]
                .fillna("")
                .str.contains(search, case=False)
                |
                guests["id_number"]
                .fillna("")
                .str.contains(search, case=False)
            )

            guests = guests[mask]

        st.dataframe(
            guests.rename(columns={
                "id": "Mã KH",
                "full_name": "Họ tên",
                "phone": "SĐT",
                "email": "Email",
                "id_number": "CCCD/Hộ chiếu",
                "address": "Địa chỉ",
                "created_at": "Ngày tạo"
            }),
            use_container_width=True,
            hide_index=True
        )

    with tab2:

        with st.form("add_guest"):

            full_name = st.text_input(
                "Họ và tên *"
            )

            col1, col2 = st.columns(2)

            phone = col1.text_input(
                "Số điện thoại"
            )

            email = col2.text_input(
                "Email"
            )

            col1, col2 = st.columns(2)

            id_number = col1.text_input(
                "CCCD / Hộ chiếu"
            )

            address = col2.text_input(
                "Địa chỉ"
            )

            submit = st.form_submit_button(
                "➕ Thêm khách",
                type="primary"
            )

            if submit:

                if not full_name.strip():

                    st.error(
                        "Vui lòng nhập họ tên."
                    )

                else:

                    execute("""
                        INSERT INTO guests
                        (
                            full_name,
                            phone,
                            email,
                            id_number,
                            address,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        full_name,
                        phone,
                        email,
                        id_number,
                        address,
                        datetime.now().isoformat()
                    ))

                    st.success(
                        "Đã thêm khách hàng."
                    )

                    st.rerun()


# ============================================================
# CHECK-IN / CHECK-OUT
# ============================================================

elif page == "🧾 Check-in / Check-out":

    st.title(
        "🧾 Check-in / Check-out"
    )

    bookings = read_df("""
        SELECT
            b.id,
            b.booking_code,
            g.full_name,
            g.phone,
            r.room_number,
            r.room_type,
            b.check_in,
            b.check_out,
            b.status,
            b.room_charge,
            b.deposit
        FROM bookings b
        JOIN guests g
            ON g.id = b.guest_id
        JOIN rooms r
            ON r.id = b.room_id
        WHERE b.status IN ('Đã đặt', 'Đang ở')
        ORDER BY b.check_in
    """)

    if bookings.empty:

        st.info(
            "Không có booking cần xử lý."
        )

    else:

        st.dataframe(
            bookings.rename(columns={
                "booking_code": "Booking",
                "full_name": "Khách",
                "phone": "SĐT",
                "room_number": "Phòng",
                "room_type": "Loại",
                "check_in": "Check-in",
                "check_out": "Check-out",
                "status": "Trạng thái",
                "room_charge": "Tiền phòng",
                "deposit": "Đặt cọc"
            }),
            use_container_width=True,
            hide_index=True
        )

        booking_map = {
            f"{row.booking_code} — "
            f"{row.full_name} — "
            f"Phòng {row.room_number}":
            int(row.id)
            for _, row in bookings.iterrows()
        }

        selected = st.selectbox(
            "Chọn booking",
            list(booking_map.keys())
        )

        booking_id = booking_map[selected]

        booking = bookings[
            bookings["id"] == booking_id
        ].iloc[0]

        col1, col2 = st.columns(2)

        # ----------------------------------------------------
        # CHECK IN
        # ----------------------------------------------------

        with col1:

            st.subheader(
                "🔵 Check-in"
            )

            st.write(
                f"Khách: **{booking['full_name']}**"
            )

            st.write(
                f"Phòng: **{booking['room_number']}**"
            )

            if booking["status"] == "Đã đặt":

                if st.button(
                    "✅ Xác nhận Check-in",
                    type="primary",
                    use_container_width=True
                ):

                    execute("""
                        UPDATE bookings
                        SET status = 'Đang ở'
                        WHERE id = ?
                    """, (booking_id,))

                    execute("""
                        UPDATE rooms
                        SET status = 'Đang ở'
                        WHERE room_number = ?
                    """, (
                        booking["room_number"],
                    ))

                    st.success(
                        "Check-in thành công."
                    )

                    st.rerun()

            else:

                st.success(
                    "Khách đang lưu trú."
                )

        # ----------------------------------------------------
        # CHECK OUT
        # ----------------------------------------------------

        with col2:

            st.subheader(
                "⚪ Check-out"
            )

            st.write(
                f"Khách: **{booking['full_name']}**"
            )

            st.write(
                f"Phòng: **{booking['room_number']}**"
            )

            if booking["status"] == "Đang ở":

                if st.button(
                    "🚪 Xác nhận Check-out",
                    type="primary",
                    use_container_width=True
                ):

                    execute("""
                        UPDATE bookings
                        SET status = 'Đã trả'
                        WHERE id = ?
                    """, (booking_id,))

                    execute("""
                        UPDATE rooms
                        SET status = 'Đang dọn'
                        WHERE room_number = ?
                    """, (
                        booking["room_number"],
                    ))

                    st.success(
                        "Check-out thành công. "
                        "Phòng đã chuyển sang Housekeeping."
                    )

                    st.rerun()

            else:

                st.warning(
                    "Khách chưa check-in."
                )


# ============================================================
# HOUSEKEEPING
# ============================================================

elif page == "🧹 Housekeeping":

    st.title(
        "🧹 Housekeeping"
    )

    st.caption(
        "Quản lý tình trạng vệ sinh và bàn giao phòng"
    )

    housekeeping = read_df("""
        SELECT
            r.id,
            r.room_number,
            r.room_type,
            r.status,
            h.cleaning_status,
            h.last_cleaned,
            h.note
        FROM rooms r
        LEFT JOIN housekeeping h
            ON r.id = h.room_id
        ORDER BY r.floor, r.room_number
    """)

    st.dataframe(
        housekeeping.rename(columns={
            "room_number": "Phòng",
            "room_type": "Loại",
            "status": "Trạng thái phòng",
            "cleaning_status": "Vệ sinh",
            "last_cleaned": "Lần dọn cuối",
            "note": "Ghi chú"
        }),
        use_container_width=True,
        hide_index=True
    )

    room_map = {
        f"Phòng {row.room_number} - {row.room_type}":
        int(row.id)
        for _, row in housekeeping.iterrows()
    }

    selected = st.selectbox(
        "Chọn phòng",
        list(room_map.keys())
    )

    room_id = room_map[selected]

    current = housekeeping[
        housekeeping["id"] == room_id
    ].iloc[0]

    cleaning_statuses = [
        "Sạch",
        "Bẩn",
        "Đang dọn",
        "Kiểm tra lại",
        "Không sử dụng"
    ]

    with st.form(
        "housekeeping_form"
    ):

        cleaning_status = st.selectbox(
            "Tình trạng vệ sinh",
            cleaning_statuses,
            index=(
                cleaning_statuses.index(
                    current["cleaning_status"]
                )
                if current["cleaning_status"]
                in cleaning_statuses
                else 0
            )
        )

        note = st.text_area(
            "Ghi chú",
            value=current["note"] or ""
        )

        submit = st.form_submit_button(
            "💾 Cập nhật",
            type="primary"
        )

        if submit:

            execute("""
                UPDATE housekeeping
                SET
                    cleaning_status = ?,
                    last_cleaned = ?,
                    note = ?
                WHERE room_id = ?
            """, (
                cleaning_status,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                ),
                note,
                room_id
            ))

            # Nếu phòng đã được vệ sinh xong
            # thì chuyển về Trống nếu trước đó đang dọn

            if (
                cleaning_status == "Sạch"
                and current["status"] == "Đang dọn"
            ):

                execute("""
                    UPDATE rooms
                    SET status = 'Trống'
                    WHERE id = ?
                """, (room_id,))

            elif cleaning_status in [
                "Bẩn",
                "Đang dọn",
                "Kiểm tra lại"
            ]:

                if current["status"] not in [
                    "Đang ở",
                    "Đã đặt",
                    "Bảo trì"
                ]:

                    execute("""
                        UPDATE rooms
                        SET status = 'Đang dọn'
                        WHERE id = ?
                    """, (room_id,))

            st.success(
                "Đã cập nhật tình trạng phòng."
            )

            st.rerun()


# ============================================================
# HÓA ĐƠN
# ============================================================

elif page == "💳 Hóa đơn":

    st.title(
        "💳 Hóa đơn & thanh toán"
    )

    bookings = read_df("""
        SELECT
            b.id,
            b.booking_code,
            g.id AS guest_id,
            g.full_name,
            r.room_number,
            b.room_charge,
            b.deposit,
            b.status
        FROM bookings b
        JOIN guests g
            ON g.id = b.guest_id
        JOIN rooms r
            ON r.id = b.room_id
        WHERE b.status = 'Đã trả'
        ORDER BY b.id DESC
    """)

    if bookings.empty:

        st.info(
            "Chưa có booking đã check-out."
        )

    else:

        tab1, tab2 = st.tabs([
            "🧾 Tạo hóa đơn",
            "📋 Lịch sử hóa đơn"
        ])

        # ----------------------------------------------------
        # TẠO HÓA ĐƠN
        # ----------------------------------------------------

        with tab1:

            booking_map = {
                f"{row.booking_code} — "
                f"{row.full_name} — "
                f"Phòng {row.room_number}":
                int(row.id)
                for _, row in bookings.iterrows()
            }

            selected = st.selectbox(
                "Booking",
                list(booking_map.keys())
            )

            booking_id = booking_map[selected]

            booking = bookings[
                bookings["id"] == booking_id
            ].iloc[0]

            col1, col2, col3 = st.columns(3)

            service_charge = col1.number_input(
                "Dịch vụ phát sinh",
                min_value=0,
                max_value=100000000,
                value=0,
                step=50000
            )

            discount = col2.number_input(
                "Giảm giá",
                min_value=0,
                max_value=100000000,
                value=0,
                step=50000
            )

            payment_method = col3.selectbox(
                "Phương thức thanh toán",
                [
                    "Tiền mặt",
                    "Chuyển khoản",
                    "Thẻ"
                ]
            )

            total = (
                float(booking["room_charge"])
                + service_charge
                - discount
            )

            remaining = max(
                total - float(booking["deposit"] or 0),
                0
            )

            st.info(
                f"Tiền phòng: {money(booking['room_charge'])}  |  "
                f"Đặt cọc: {money(booking['deposit'])}  |  "
                f"Còn lại: {money(remaining)}"
            )

            st.metric(
                "TỔNG THANH TOÁN",
                money(total)
            )

            if st.button(
                "🧾 Phát hành hóa đơn",
                type="primary"
            ):

                existing = execute("""
                    SELECT *
                    FROM invoices
                    WHERE booking_id = ?
                """, (booking_id,), fetch=True)

                if existing:

                    st.warning(
                        "Booking này đã có hóa đơn."
                    )

                else:

                    invoice_number = create_invoice_number()

                    execute("""
                        INSERT INTO invoices
                        (
                            invoice_number,
                            booking_id,
                            room_charge,
                            service_charge,
                            discount,
                            total,
                            payment_method,
                            payment_status,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        invoice_number,
                        booking_id,
                        booking["room_charge"],
                        service_charge,
                        discount,
                        total,
                        payment_method,
                        "Đã thanh toán",
                        datetime.now().isoformat()
                    ))

                    st.success(
                        f"Đã phát hành hóa đơn {invoice_number}"
                    )

                    st.rerun()

        # ----------------------------------------------------
        # LỊCH SỬ HÓA ĐƠN
        # ----------------------------------------------------

        with tab2:

            invoices = read_df("""
                SELECT
                    i.invoice_number,
                    g.full_name,
                    r.room_number,
                    i.room_charge,
                    i.service_charge,
                    i.discount,
                    i.total,
                    i.payment_method,
                    i.payment_status,
                    i.created_at
                FROM invoices i
                JOIN bookings b
                    ON b.id = i.booking_id
                JOIN guests g
                    ON g.id = b.guest_id
                JOIN rooms r
                    ON r.id = b.room_id
                ORDER BY i.id DESC
            """)

            if invoices.empty:

                st.info(
                    "Chưa có hóa đơn."
                )

            else:

                st.dataframe(
                    invoices.rename(columns={
                        "invoice_number": "Số HĐ",
                        "full_name": "Khách",
                        "room_number": "Phòng",
                        "room_charge": "Tiền phòng",
                        "service_charge": "Dịch vụ",
                        "discount": "Giảm giá",
                        "total": "Tổng cộng",
                        "payment_method": "Thanh toán",
                        "payment_status": "Trạng thái",
                        "created_at": "Ngày tạo"
                    }),
                    use_container_width=True,
                    hide_index=True
                )


# ============================================================
# BÁO CÁO
# ============================================================

elif page == "📈 Báo cáo":

    st.title(
        "📈 Báo cáo quản trị"
    )

    rooms = read_df(
        "SELECT * FROM rooms"
    )

    bookings = read_df(
        "SELECT * FROM bookings"
    )

    invoices = read_df(
        "SELECT * FROM invoices"
    )

    total_revenue = 0

    if not invoices.empty:

        total_revenue = invoices[
            invoices["payment_status"]
            == "Đã thanh toán"
        ]["total"].sum()

    completed_bookings = len(
        bookings[
            bookings["status"] == "Đã trả"
        ]
    ) if not bookings.empty else 0

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "💰 Tổng doanh thu",
        money(total_revenue)
    )

    col2.metric(
        "📅 Tổng booking",
        len(bookings)
    )

    col3.metric(
        "🧾 Booking hoàn tất",
        completed_bookings
    )

    st.divider()

    # --------------------------------------------------------
    # DOANH THU
    # --------------------------------------------------------

    if not invoices.empty:

        invoices["created_at"] = pd.to_datetime(
            invoices["created_at"],
            errors="coerce"
        )

        revenue_by_day = (
            invoices[
                invoices["payment_status"]
                == "Đã thanh toán"
            ]
            .groupby(
                invoices["created_at"].dt.date
            )["total"]
            .sum()
        )

        st.subheader(
            "💰 Doanh thu theo ngày"
        )

        st.line_chart(
            revenue_by_day
        )

    # --------------------------------------------------------
    # TRẠNG THÁI BOOKING
    # --------------------------------------------------------

    if not bookings.empty:

        st.subheader(
            "📅 Trạng thái booking"
        )

        booking_status = (
            bookings["status"]
            .value_counts()
        )

        st.bar_chart(
            booking_status
        )

    # --------------------------------------------------------
    # TRẠNG THÁI PHÒNG
    # --------------------------------------------------------

    st.subheader(
        "🛏️ Tình trạng phòng"
    )

    room_status = (
        rooms["status"]
        .value_counts()
    )

    st.bar_chart(
        room_status
    )


# ============================================================
# QUẢN LÝ PHÒNG
# ============================================================

elif page == "⚙️ Quản lý phòng":

    st.title(
        "⚙️ Quản lý phòng"
    )

    tab1, tab2 = st.tabs([
        "📋 Danh sách phòng",
        "➕ Thêm phòng"
    ])

    # --------------------------------------------------------
    # DANH SÁCH PHÒNG
    # --------------------------------------------------------

    with tab1:

        rooms = read_df("""
            SELECT *
            FROM rooms
            ORDER BY floor, room_number
        """)

        st.dataframe(
            rooms.rename(columns={
                "id": "ID",
                "room_number": "Số phòng",
                "room_type": "Loại phòng",
                "floor": "Tầng",
                "price": "Giá/đêm",
                "capacity": "Sức chứa",
                "status": "Trạng thái",
                "note": "Ghi chú"
            }),
            use_container_width=True,
            hide_index=True
        )

        st.subheader(
            "✏️ Cập nhật phòng"
        )

        room_map = {
            f"Phòng {row.room_number} - {row.room_type}":
            int(row.id)
            for _, row in rooms.iterrows()
        }

        selected = st.selectbox(
            "Chọn phòng",
            list(room_map.keys())
        )

        room_id = room_map[selected]

        room = rooms[
            rooms["id"] == room_id
        ].iloc[0]

        with st.form("edit_room"):

            col1, col2, col3 = st.columns(3)

            room_type = col1.selectbox(
                "Loại phòng",
                [
                    "Standard",
                    "Superior",
                    "Deluxe",
                    "Suite"
                ],
                index=[
                    "Standard",
                    "Superior",
                    "Deluxe",
                    "Suite"
                ].index(room["room_type"])
            )

            floor = col2.number_input(
                "Tầng",
                min_value=1,
                max_value=100,
                value=int(room["floor"])
            )

            price = col3.number_input(
                "Giá/đêm",
                min_value=0,
                max_value=100000000,
                value=int(room["price"]),
                step=50000
            )

            col1, col2 = st.columns(2)

            capacity = col1.number_input(
                "Sức chứa",
                min_value=1,
                max_value=20,
                value=int(room["capacity"])
            )

            status = col2.selectbox(
                "Trạng thái",
                [
                    "Trống",
                    "Đã đặt",
                    "Đang ở",
                    "Đang dọn",
                    "Bảo trì"
                ],
                index=[
                    "Trống",
                    "Đã đặt",
                    "Đang ở",
                    "Đang dọn",
                    "Bảo trì"
                ].index(room["status"])
            )

            note = st.text_area(
                "Ghi chú",
                value=room["note"] or ""
            )

            submit = st.form_submit_button(
                "💾 Lưu thay đổi",
                type="primary"
            )

            if submit:

                execute("""
                    UPDATE rooms
                    SET
                        room_type = ?,
                        floor = ?,
                        price = ?,
                        capacity = ?,
                        status = ?,
                        note = ?
                    WHERE id = ?
                """, (
                    room_type,
                    floor,
                    price,
                    capacity,
                    status,
                    note,
                    room_id
                ))

                st.success(
                    "Đã cập nhật phòng."
                )

                st.rerun()

    # --------------------------------------------------------
    # THÊM PHÒNG
    # --------------------------------------------------------

    with tab2:

        with st.form("add_room"):

            room_number = st.text_input(
                "Số phòng *"
            )

            col1, col2 = st.columns(2)

            room_type = col1.selectbox(
                "Loại phòng",
                [
                    "Standard",
                    "Superior",
                    "Deluxe",
                    "Suite"
                ]
            )

            floor = col2.number_input(
                "Tầng",
                min_value=1,
                max_value=100,
                value=1
            )

            col1, col2 = st.columns(2)

            price = col1.number_input(
                "Giá/đêm",
                min_value=0,
                max_value=100000000,
                value=800000,
                step=50000
            )

            capacity = col2.number_input(
                "Sức chứa",
                min_value=1,
                max_value=20,
                value=2
            )

            note = st.text_area(
                "Ghi chú"
            )

            submit = st.form_submit_button(
                "➕ Thêm phòng",
                type="primary"
            )

            if submit:

                if not room_number.strip():

                    st.error(
                        "Vui lòng nhập số phòng."
                    )

                else:

                    try:

                        room_id = execute("""
                            INSERT INTO rooms
                            (
                                room_number,
                                room_type,
                                floor,
                                price,
                                capacity,
                                status,
                                note
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            room_number.strip(),
                            room_type,
                            floor,
                            price,
                            capacity,
                            "Trống",
                            note
                        ))

                        execute("""
                            INSERT INTO housekeeping
                            (
                                room_id,
                                cleaning_status,
                                last_cleaned
                            )
                            VALUES (?, ?, ?)
                        """, (
                            room_id,
                            "Sạch",
                            datetime.now().strftime(
                                "%Y-%m-%d %H:%M"
                            )
                        ))

                        st.success(
                            f"Đã thêm phòng {room_number}."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "Số phòng đã tồn tại."
                        )
