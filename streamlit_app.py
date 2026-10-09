import streamlit as st
import sqlite3
import pandas as pd

DB="toko_iman.db"

def get_conn():
    conn=sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory=sqlite3.Row
    return conn

def init_db():
    conn=get_conn(); c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS produk (barcode TEXT PRIMARY KEY, nama TEXT, harga INTEGER, stok INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS transaksi (id INTEGER PRIMARY KEY AUTOINCREMENT, total INTEGER, waktu TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c.execute("CREATE TABLE IF NOT EXISTS saldo_kasir (id INTEGER PRIMARY KEY, saldo INTEGER)")
    c.execute("SELECT COUNT(*) FROM produk")
    if c.fetchone()[0]==0:
        c.execute("INSERT INTO produk VALUES ('8991002100014','Indomie Goreng',3500,100)")
        c.execute("INSERT INTO produk VALUES ('8991002100021','Aqua 600ml',3000,50)")
    c.execute("SELECT COUNT(*) FROM saldo_kasir")
    if c.fetchone()[0]==0: c.execute("INSERT INTO saldo_kasir VALUES (1,0)")
    conn.commit(); conn.close()

def get_saldo():
    conn=get_conn()
    try:
        df=pd.read_sql("SELECT saldo FROM saldo_kasir WHERE id=1", conn)
        return int(df.iloc[0]['saldo']) if not df.empty else 0
    except: return 0
    finally: conn.close()

def update_saldo(jumlah):
    conn=get_conn()
    conn.execute("UPDATE saldo_kasir SET saldo = saldo +? WHERE id=1", (jumlah,))
    conn.commit(); conn.close()

init_db()
st.set_page_config(page_title="TOKO IMAN", layout="wide")

st.sidebar.title("TOKO IMAN ULTRA")
saldo = get_saldo()
st.sidebar.metric("SALDO KASIR REALTIME", f"Rp {saldo:,}")

menu=st.sidebar.selectbox("Menu", ["KASIR POS", "TRANSAKSI ONLINE", "LAPORAN"])

conn=get_conn()

if menu=="KASIR POS":
    st.title("KASIR POS")
    if 'cart' not in st.session_state: st.session_state.cart=[]

    cari=st.text_input("Scan Barcode / Nama Produk")
    if cari:
        cur=conn.cursor()
        cur.execute("SELECT * FROM produk WHERE barcode LIKE? OR nama LIKE?", (f"%{cari}%", f"%{cari}%"))
        rows=cur.fetchall()
        for r in rows:
            col1,col2,col3=st.columns([3,1,1])
            col1.write(f"{r['nama']} - Rp {r['harga']:,}")
            qty=col2.number_input("qty",1,r['stok'],1,key=f"qty_{r['barcode']}")
            if col3.button("Tambah", key=f"add_{r['barcode']}"):
                st.session_state.cart.append({"nama":r['nama'],"harga":r['harga'],"qty":qty,"subtotal":r['harga']*qty})
                st.rerun()

    if st.session_state.cart:
        df=pd.DataFrame(st.session_state.cart)
        st.dataframe(df, use_container_width=True)
        total=sum(x['subtotal'] for x in st.session_state.cart)
        st.metric("TOTAL BAYAR", f"Rp {total:,}")
        if st.button("BAYAR - SALDO AUTO UPDATE", type="primary", use_container_width=True):
            conn.execute("INSERT INTO transaksi (total) VALUES (?)", (total,))
            conn.commit()
            update_saldo(total)
            st.session_state.cart=[]
            st.success("Transaksi sukses! Saldo update realtime!")
            st.rerun()

elif menu=="TRANSAKSI ONLINE":
    st.title("TRANSAKSI ONLINE")
    st.info("Fitur ini bikin saldo kasir masuk otomatis kalau ada transfer QRIS / GoPay / DANA")
    nominal=st.number_input("Nominal Pembayaran Online Masuk", min_value=0, step=1000)
    if st.button("Konfirmasi Pembayaran Online Masuk"):
        update_saldo(nominal)
        st.success(f"Rp {nominal:,} masuk! Saldo sekarang Rp {get_saldo():,}")
        st.rerun()

else:
    st.title("LAPORAN")
    st.dataframe(pd.read_sql("SELECT * FROM transaksi ORDER BY id DESC", conn))
