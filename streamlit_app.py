import streamlit as st, sqlite3, pandas as pd, datetime
from datetime import date
import plotly.express as px
import streamlit.components.v1 as components
st.set_page_config(page_title="TOKO IMAN ULTRA", page_icon="🏪", layout="wide")
DB="toko_iman.db"
def get_conn():
    conn=sqlite3.connect(DB,check_same_thread=False);conn.row_factory=sqlite3.Row;return conn
def init_db():
    conn=get_conn();c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS produk (id INTEGER PRIMARY KEY AUTOINCREMENT, barcode TEXT UNIQUE, nama TEXT, kategori TEXT, harga_beli INTEGER, harga_jual INTEGER, stok INTEGER, satuan TEXT, lokasi TEXT, supplier TEXT, exp DATE, min_stok INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS transaksi (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, invoice TEXT UNIQUE, total INTEGER, bayar INTEGER, kembalian INTEGER, metode TEXT, member TEXT, kasir TEXT, diskon INTEGER, laba INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS detail_transaksi (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice TEXT, barcode TEXT, nama TEXT, qty INTEGER, harga INTEGER, subtotal INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS member (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, hp TEXT UNIQUE, poin INTEGER DEFAULT 0, alamat TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS saldo_kasir (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, keterangan TEXT, jenis TEXT, jumlah INTEGER, saldo_akhir INTEGER, kasir TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS layanan_digital (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, invoice TEXT, jenis TEXT, provider TEXT, no_tujuan TEXT, nominal INTEGER, harga_jual INTEGER, admin INTEGER, laba INTEGER, status TEXT, pelanggan TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, user TEXT, aksi TEXT, modul TEXT, detail TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS emoney_topup (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, invoice TEXT, jenis_emoney TEXT, no_kartu TEXT, nominal INTEGER, harga_jual INTEGER, laba INTEGER)")
    c.execute("SELECT COUNT(*) FROM produk")
    if c.fetchone()[0]==0:
        sample=[("8991002100014","Indomie Goreng","Makanan",2800,3500,120,"pcs","Rak A1","Indofood","2026-12-31",10),("8991001130012","Aqua 600ml","Minuman",2500,3500,80,"pcs","Kulkas","Aqua","2026-11-01",15),("8992761100015","Beras 5kg","Sembako",58000,65000,25,"karung","Rak B2","Sania","2026-10-10",5)]
        for s in sample: c.execute("INSERT OR IGNORE INTO produk(barcode,nama,kategori,harga_beli,harga_jual,stok,satuan,lokasi,supplier,exp,min_stok) VALUES(?,?,?,?,?,?,?,?,?,?,?)",s)
    c.execute("SELECT COUNT(*) FROM saldo_kasir")
    if c.fetchone()[0]==0: c.execute("INSERT INTO saldo_kasir(tanggal,keterangan,jenis,jumlah,saldo_akhir,kasir) VALUES(?,?,?,?,?,?)",(datetime.datetime.now().isoformat(),"Modal Awal","masuk",2000000,2000000,"Iman"))
    conn.commit();conn.close()
def audit(user,aksi,modul,detail):
    conn=get_conn();conn.execute("INSERT INTO audit_log(tanggal,user,aksi,modul,detail) VALUES(?,?,?,?,?)",(datetime.datetime.now().isoformat(),user,aksi,modul,detail));conn.commit();conn.close()
def get_saldo():
    conn=get_conn();df=pd.read_sql("SELECT * FROM saldo_kasir ORDER BY id DESC LIMIT 1",conn);conn.close();return df.iloc[0]['saldo_akhir'] if not df.empty else 0
init_db();conn=get_conn()
st.sidebar.title("🏪 TOKO IMAN ULTRA");st.sidebar.caption("NFC + BT Printer + E-Money");menu=st.sidebar.radio("MENU",["🛒 KASIR POS","💳 PPOB + E-Money Topup","💰 Saldo Kasir + Topup","🖨️ Koneksi Printer & NFC","📦 Stok","📊 Dashboard & Audit","🧾 History"]);saldo=get_saldo();st.sidebar.metric("💰 SALDO KASIR",f"Rp {saldo:,}")

if menu=="🛒 KASIR POS":
    st.title("🛒 KASIR POS")
    if 'cart' not in st.session_state: st.session_state.cart=[]
    c1,c2=st.columns([2,1])
    with c1:
        bc=st.text_input("🔍 Scan Barcode / Nama")
        if bc:
            cur=conn.cursor();cur.execute("SELECT * FROM produk WHERE barcode LIKE? OR nama LIKE? LIMIT 10",(f"%{bc}%",f"%{bc}%"))
            for r in cur.fetchall():
                a,b,c=st.columns([3,1,1]);a.write(f"**{r['nama']}** Rp{r['harga_jual']:,} Stok:{r['stok']}")
                q=b.number_input("q",1,r['stok'],1,key=f"q{r['barcode']}",label_visibility="collapsed")
                if c.button("Tambah",key=f"add{r['barcode']}"):
                    st.session_state.cart.append({"barcode":r['barcode'],"nama":r['nama'],"harga":r['harga_jual'],"hb":r['harga_beli'],"qty":q,"subtotal":r['harga_jual']*q});audit("Iman","Tambah Keranjang","KASIR",f"{r['nama']} x{q}");st.rerun()
        if st.session_state.cart:
            st.dataframe(pd.DataFrame(st.session_state.cart),use_container_width=True)
            st.metric("TOTAL",f"Rp {sum(x['subtotal'] for x in st.session_state.cart):,}")
            if st.button("Kosongkan"): st.session_state.cart=[];st.rerun()
    with c2:
        total=sum(x['subtotal'] for x in st.session_state.cart) if st.session_state.cart else 0
        laba=sum((x['harga']-x['hb'])*x['qty'] for x in st.session_state.cart) if st.session_state.cart else 0
        metode=st.selectbox("Metode Bayar",["Tunai","QRIS","Transfer","Debit","E-Money / NFC"])
        bayar=st.number_input("Bayar",value=total);kembalian=bayar-total
        st.write(f"Kembali Rp {kembalian:,}")
        if st.button("💾 BAYAR & PRINT",type="primary",disabled=len(st.session_state.cart)==0 or kembalian<0):
            inv=f"IMN-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}";cur=conn.cursor()
            cur.execute("INSERT INTO transaksi(tanggal,invoice,total,bayar,kembalian,metode,member,kasir,diskon,laba) VALUES(?,?,?,?,?,?,?,?,?,?)",(datetime.datetime.now().isoformat(),inv,total,bayar,kembalian,metode,"","Iman",0,laba))
            for it in st.session_state.cart:
                cur.execute("INSERT INTO detail_transaksi(invoice,barcode,nama,qty,harga,subtotal) VALUES(?,?,?,?,?,?)",(inv,it['barcode'],it['nama'],it['qty'],it['harga'],it['subtotal']))
                cur.execute("UPDATE produk SET stok=stok-? WHERE barcode=?",(it['qty'],it['barcode']))
            new_saldo=get_saldo()+total
            cur.execute("INSERT INTO saldo_kasir(tanggal,keterangan,jenis,jumlah,saldo_akhir,kasir) VALUES(?,?,?,?,?,?)",(datetime.datetime.now().isoformat(),f"Penjualan {inv}","masuk",total,new_saldo,"Iman"))
            conn.commit();audit("Iman","Transaksi","KASIR",f"{inv} Rp{total:,}");st.success(f"{inv} Sukses!");st.balloons()
            st.session_state.cart=[]

elif menu=="💳 PPOB + E-Money Topup":
    st.title("💳 Topup Saldo, E-Money, Pulsa, Token")
    tab1,tab2=st.tabs(["🔋 Topup E-Money & Saldo","📱 Pulsa / Paket / Token / Transfer"])
    with tab1:
        jenis_emoney=st.selectbox("Jenis", ["GoPay","OVO","DANA","ShopeePay","LinkAja","E-Money Mandiri","Flazz BCA","Brizzi BRI","TapCash BNI","Saldo Kasir Toko (Topup Modal)"])
        no_kartu=st.text_input("No HP / No Kartu")
        nominal=st.selectbox("Nominal", [10000,20000,50000,100000,200000,500000,1000000])
        admin=st.number_input("Admin Fee", value=2000)
        harga_jual=nominal+admin+1500
        st.metric("Harga Jual", f"Rp {harga_jual:,} Laba {harga_jual-nominal:,}")
        if st.button("💾 Proses Topup", type="primary"):
            inv=f"EMON-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}";cur=conn.cursor()
            if "Saldo Kasir" in jenis_emoney:
                new_saldo=get_saldo()+nominal
                cur.execute("INSERT INTO saldo_kasir(tanggal,keterangan,jenis,jumlah,saldo_akhir,kasir) VALUES(?,?,?,?,?,?)",(datetime.datetime.now().isoformat(),f"Topup Saldo {nominal}","masuk",nominal,new_saldo,"Iman"))
                conn.commit();st.success(f"Saldo Topup Rp{nominal:,} Baru Rp{new_saldo:,}")
            else:
                cur.execute("INSERT INTO emoney_topup(tanggal,invoice,jenis_emoney,no_kartu,nominal,harga_jual,laba) VALUES(?,?,?,?,?,?,?)",(datetime.datetime.now().isoformat(),inv,jenis_emoney,no_kartu,nominal,harga_jual,harga_jual-nominal))
                cur.execute("INSERT INTO layanan_digital(tanggal,invoice,jenis,provider,no_tujuan,nominal,harga_jual,admin,laba,status,pelanggan) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(datetime.datetime.now().isoformat(),inv,"Topup E-Money",jenis_emoney,no_kartu,nominal,harga_jual,admin,harga_jual-nominal,"Sukses","Pelanggan"))
                new_saldo=get_saldo()+harga_jual
                cur.execute("INSERT INTO saldo_kasir(tanggal,keterangan,jenis,jumlah,saldo_akhir,kasir) VALUES(?,?,?,?,?,?)",(datetime.datetime.now().isoformat(),f"Topup {jenis_emoney}","masuk",harga_jual,new_saldo,"Iman"))
                conn.commit();st.success(f"Topup {jenis_emoney} Rp{nominal:,} Berhasil!")
    with tab2:
        jenis=st.selectbox("Layanan", ["Transfer Bank","Pulsa","Paket Data","Token Listrik"])
        prov=st.text_input("Tujuan"); nom=st.number_input("Nominal Modal",0); jual=st.number_input("Harga Jual",value=nom+2500)
        if st.button("Simpan PPOB"):
            inv=f"PPOB-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            conn.execute("INSERT INTO layanan_digital(tanggal,invoice,jenis,provider,no_tujuan,nominal,harga_jual,admin,laba,status,pelanggan) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(datetime.datetime.now().isoformat(),inv,jenis,prov,prov,nom,jual,2500,jual-nom,"Sukses","Pelanggan"))
            new_saldo=get_saldo()+jual;conn.execute("INSERT INTO saldo_kasir(tanggal,keterangan,jenis,jumlah,saldo_akhir,kasir) VALUES(?,?,?,?,?,?)",(datetime.datetime.now().isoformat(),f"{jenis} {prov}","masuk",jual,new_saldo,"Iman"));conn.commit();st.success(f"Berhasil {inv}")

elif menu=="💰 Saldo Kasir + Topup":
    st.title("💰 Saldo Kasir + Topup Instan")
    st.metric("Saldo Sekarang", f"Rp {saldo:,}")
    c1,c2,c3,c4=st.columns(4)
    if c1.button("➕ 100K"): conn.execute("INSERT INTO saldo_kasir(tanggal,keterangan,jenis,jumlah,saldo_akhir,kasir) VALUES(?,?,?,?,?,?)",(datetime.datetime.now().isoformat(),"Topup 100K","masuk",100000,saldo+100000,"Iman"));conn.commit();st.rerun()
    if c2.button("➕ 500K"): conn.execute("INSERT INTO saldo_kasir(tanggal,keterangan,jenis,jumlah,saldo_akhir,kasir) VALUES(?,?,?,?,?,?)",(datetime.datetime.now().isoformat(),"Topup 500K","masuk",500000,saldo+500000,"Iman"));conn.commit();st.rerun()
    if c3.button("➕ 1 Jt"): conn.execute("INSERT INTO saldo_kasir(tanggal,keterangan,jenis,jumlah,saldo_akhir,kasir) VALUES(?,?,?,?,?,?)",(datetime.datetime.now().isoformat(),"Topup 1Jt","masuk",1000000,saldo+1000000,"Iman"));conn.commit();st.rerun()
    if c4.button("➖ 100K"): conn.execute("INSERT INTO saldo_kasir(tanggal,keterangan,jenis,jumlah,saldo_akhir,kasir) VALUES(?,?,?,?,?,?)",(datetime.datetime.now().isoformat(),"Tarik","keluar",100000,saldo-100000,"Iman"));conn.commit();st.rerun()
    st.dataframe(pd.read_sql("SELECT * FROM saldo_kasir ORDER BY id DESC LIMIT 50",conn),use_container_width=True)

elif menu=="🖨️ Koneksi Printer & NFC":
    st.title("🖨️ Bluetooth Printer & NFC")
    st.info("Butuh Android Chrome + Printer 58mm Bluetooth")
    components.html('<div style="padding:15px;border:1px solid #ccc;border-radius:10px;"><h3>🖨️ Bluetooth Printer</h3><button id="btBtn" style="padding:12px 20px;background:#000;color:white;border-radius:8px;width:100%;">🔍 Konek Printer</button><p id="btStatus"></p><textarea id="printText" style="width:100%;height:100px;">TOKO IMAN Test Print OK!</textarea><button id="printBtn" style="margin-top:10px;padding:10px;width:100%;background:#00C853;color:white;border:none;border-radius:8px;">🖨️ PRINT TEST</button></div><script>let printerDevice=null;document.getElementById("btBtn").onclick=async()=>{try{printerDevice=await navigator.bluetooth.requestDevice({acceptAllDevices:true,optionalServices:["000018f0-0000-1000-8000-00805f9b34fb","0000ff00-0000-1000-8000-00805f9b34fb"]});const server=await printerDevice.gatt.connect();document.getElementById("btStatus").innerText="✅ Terhubung: "+printerDevice.name;window.btServer=server;}catch(e){document.getElementById("btStatus").innerText="❌ Gagal: "+e}};document.getElementById("printBtn").onclick=async()=>{const text=document.getElementById("printText").value;if(window.btServer){try{const services=await window.btServer.getPrimaryServices();for(let s of services){let chars=await s.getCharacteristics();for(let c of chars){if(c.properties.write){let enc=new TextEncoder().encode(text+"\\n\\n\\n");await c.writeValue(enc);document.getElementById("btStatus").innerText="🖨️ Print dikirim!";return;}}}}catch(e){document.getElementById("btStatus").innerText="❌ Error: "+e}}else{let w=window.open("","","width=300,height=600");w.document.write("<pre>"+text+"</pre>");w.document.close();w.print();}};</script>',height=400)

elif menu=="📦 Stok":
    st.dataframe(pd.read_sql("SELECT * FROM produk",conn),use_container_width=True)
elif menu=="📊 Dashboard & Audit":
    df_t=pd.read_sql("SELECT * FROM transaksi",conn); df_p=pd.read_sql("SELECT * FROM layanan_digital",conn)
    c1,c2,c3=st.columns(3)
    c1.metric("Omzet Toko",f"Rp {df_t['total'].sum() if not df_t.empty else 0:,}")
    c2.metric("Omzet PPOB",f"Rp {df_p['harga_jual'].sum() if not df_p.empty else 0:,}")
    c3.metric("Saldo",f"Rp {saldo:,}")
    st.dataframe(pd.read_sql("SELECT * FROM audit_log ORDER BY id DESC LIMIT 100",conn),use_container_width=True)
elif menu=="🧾 History":
    st.dataframe(pd.read_sql("SELECT * FROM saldo_kasir ORDER BY id DESC",conn),use_container_width=True)
