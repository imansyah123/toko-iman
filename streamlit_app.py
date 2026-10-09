import streamlit as st
import sqlite3
import pandas as pd
import time
from datetime import datetime

DB="toko_iman_ultra.db"

def get_conn():
    conn=sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory=sqlite3.Row
    return conn

def init_db():
    conn=get_conn(); c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS produk (barcode TEXT PRIMARY KEY, nama TEXT, harga INTEGER, stok INTEGER, kategori TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS saldo_kasir (id INTEGER PRIMARY KEY, saldo INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS transaksi (id INTEGER PRIMARY KEY AUTOINCREMENT, jenis TEXT, detail TEXT, total INTEGER, metode TEXT, waktu TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c.execute("SELECT COUNT(*) FROM produk")
    if c.fetchone()[0]==0:
        sample=[("8991002100014","Indomie Goreng",3500,100,"Makanan"),("8991002100021","Aqua 600ml",3000,50,"Minuman"),("8992761001012","Beras 5kg",65000,20,"Sembako")]
        for s in sample: c.execute("INSERT OR IGNORE INTO produk VALUES (?,?,?,?,?)", s)
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

def update_saldo(j):
    conn=get_conn(); conn.execute("UPDATE saldo_kasir SET saldo=saldo+? WHERE id=1",(j,)); conn.commit(); conn.close()

def add_trx(jenis,detail,total,metode):
    conn=get_conn(); conn.execute("INSERT INTO transaksi (jenis,detail,total,metode) VALUES (?,?,?,?)",(jenis,detail,total,metode)); conn.commit(); conn.close()

init_db()
st.set_page_config(page_title="TOKO IMAN ULTRA", layout="wide")
st.sidebar.title("TOKO IMAN ULTRA")
st.sidebar.metric("SALDO REALTIME", f"Rp {get_saldo():,}")
menu=st.sidebar.selectbox("MENU", ["KASIR POS","NFC READER","BANK / E-WALLET","PULSA / PAKET DATA","PLN TOKEN & TAGIHAN","ETOL / EMONEY","STOK / TAMBAH BARANG","AUDIT & LAPORAN"])
conn=get_conn()

if menu=="KASIR POS":
    st.title("KASIR POS")
    if 'cart' not in st.session_state: st.session_state.cart=[]
    cari=st.text_input("Scan Barcode / Nama")
    if cari:
        cur=conn.cursor(); cur.execute("SELECT * FROM produk WHERE barcode LIKE? OR nama LIKE?", (f"%{cari}%",f"%{cari}%"))
        for r in cur.fetchall():
            c1,c2,c3=st.columns([3,1,1])
            c1.write(f"{r['nama']} - Rp {r['harga']:,} Stok:{r['stok']}")
            qty=c2.number_input("qty",1,r['stok'],1,key=f"q{r['barcode']}")
            if c3.button("Tambah",key=f"a{r['barcode']}"):
                st.session_state.cart.append({"nama":r['nama'],"harga":r['harga'],"qty":qty,"subtotal":r['harga']*qty}); st.rerun()
    if st.session_state.cart:
        df=pd.DataFrame(st.session_state.cart); st.dataframe(df,use_container_width=True)
        total=sum(x['subtotal'] for x in st.session_state.cart)
        st.metric("TOTAL",f"Rp {total:,}")
        metode=st.selectbox("Metode", ["Tunai","BCA","BRI","DANA","GoPay","OVO","ShopeePay","QRIS"])
        if st.button("BAYAR",type="primary",use_container_width=True):
            add_trx("KASIR",str(df['nama'].tolist()),total,metode); update_saldo(total)
            st.session_state.cart=[]; st.success("Berhasil!"); st.rerun()

elif menu=="NFC READER":
    st.title("NFC READER - eMoney/Flazz/Brizzi")
    nfc=st.text_input("Tempel Kartu NFC - ID Kartu")
    if st.button("Baca Kartu"):
        if nfc:
            st.success(f"Kartu Terdeteksi: {nfc}"); st.metric("Saldo Kartu","Rp 125.000")
            nom=st.number_input("Nominal Topup",0,1000000,20000,5000)
            if st.button("Topup eMoney"):
                add_trx("NFC",nfc,nom,"NFC"); update_saldo(nom); st.success("Topup sukses!"); st.rerun()

elif menu=="BANK / E-WALLET":
    st.title("BANK / E-WALLET")
    n=st.number_input("Nominal Masuk",0,step=1000); b=st.selectbox("Bank", ["BCA","BRI","DANA","GoPay","OVO","ShopeePay","QRIS"])
    if st.button("Uang Masuk"):
        add_trx("BANK_MASUK",b,n,b); update_saldo(n); st.success(f"Rp {n:,} masuk"); st.rerun()

elif menu=="PULSA / PAKET DATA":
    st.title("PULSA / PAKET DATA")
    hp=st.text_input("No HP"); prov=st.selectbox("Provider",["Telkomsel","Indosat","XL","Tri"]); lay=st.selectbox("Paket",["Pulsa 10k (11000)","Pulsa 25k (26500)","Data 5GB (55000)","Data 10GB (85000)"])
    h=int(lay.split("(")[1].replace(")","")) if "(" in lay else 0
    if st.button("Proses Pulsa"): add_trx("PULSA",f"{prov}-{hp}-{lay}",h,"DIGITAL"); update_saldo(h); st.success("Pulsa berhasil!")

elif menu=="PLN TOKEN & TAGIHAN":
    st.title("PLN"); idp=st.text_input("ID Pelanggan"); j=st.selectbox("Jenis",["Token 20k (22000)","Token 50k (52000)","Token 100k (102000)"])
    hp=int(j.split("(")[1].replace(")","")) if "(" in j else 0
    if st.button("Proses PLN"): add_trx("PLN",idp,hp,"PLN"); update_saldo(hp); st.code("TOKEN: 1234-5678-9012-3456"); st.success("PLN berhasil!")

elif menu=="ETOL / EMONEY":
    st.title("ETOL / EMONEY"); kart=st.text_input("No Kartu"); nom=st.selectbox("Nominal",[20000,50000,100000])
    if st.button("Topup"): add_trx("ETOL",kart,nom,"ETOL"); update_saldo(nom); st.success("Topup eToll berhasil!")

elif menu=="STOK / TAMBAH BARANG":
    st.title("STOK / TAMBAH BARANG")
    st.dataframe(pd.read_sql("SELECT * FROM produk",conn),use_container_width=True)
    st.divider(); st.subheader("Tambah / Edit Barang")
    with st.form("form_produk"):
        bc=st.text_input("Barcode (Scan)")
        nm=st.text_input("Nama Barang")
        hg=st.number_input("Harga Jual",0); stk=st.number_input("Stok",0); kat=st.selectbox("Kategori",["Makanan","Minuman","Sembako","Pulsa","Lainnya"])
        s1,s2=st.columns(2)
        tambah=s1.form_submit_button("Tambah / Update Barang",type="primary",use_container_width=True)
        hapus=s2.form_submit_button("Hapus Barang",use_container_width=True)
        if tambah and bc and nm:
            conn.execute("INSERT OR REPLACE INTO produk VALUES (?,?,?,?,?)",(bc,nm,hg,stk,kat)); conn.commit(); st.success(f"{nm} disimpan!"); st.rerun()
        if hapus and bc:
            conn.execute("DELETE FROM produk WHERE barcode=?",(bc,)); conn.commit(); st.warning("Barang dihapus!"); st.rerun()

else:
    st.title("AUDIT & LAPORAN")
    df=pd.read_sql("SELECT * FROM transaksi ORDER BY id DESC",conn); st.dataframe(df,use_container_width=True)
    tot=pd.read_sql("SELECT SUM(total) as t FROM transaksi WHERE date(waktu)=date('now')",conn)
    st.metric("Omset Hari Ini", f"Rp {tot.iloc[0]['t'] or 0:,}")
    st.metric("Saldo Kasir", f"Rp {get_saldo():,}")
