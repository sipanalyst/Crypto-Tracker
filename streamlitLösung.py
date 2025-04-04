import streamlit as st
import pandas as pd
import requests as r
import sqlite3
import altair as alt


# Aufgabe 1 - benutzeroberfläche vorbereiten
st.title("Krypto-Tracker mit CoinGecko API")

# Aufgabe 2 - Kursdaten abrufen
def get_price(coin_id: str):
    BASE_URL = "https://api.coingecko.com/api/v3/"
    ENDPOINT = f"simple/price?ids={coin_id}&vs_currencies=eur"
    url = BASE_URL + ENDPOINT

    try:
        response = r.get(url, timeout=5)
        response.raise_for_status()  # Fehler bei HTTP-Fehlercodes
        data = response.json()

        if coin_id in data and "eur" in data[coin_id]:
            price = data[coin_id]["eur"]
            st.write(f"💶 Aktueller Preis von **{coin_id}**: {price} €")
            return price
        else:
            st.warning(f"Keine Preisdaten für '{coin_id}' gefunden.")
            return None

    except r.exceptions.Timeout:
        st.error("⏱️ Zeitüberschreitung bei der API-Anfrage.")
    except r.exceptions.RequestException as e:
        st.error(f"🌐 Netzwerkfehler: {e}")
    except Exception as e:
        st.error(f"❌ Unerwarteter Fehler: {e}")

    return None


#Aufgabe 3 - Datenbank erstellen und speichern

def create_database():
    try:
        conn = sqlite3.connect("crypto.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preise (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coin TEXT,
                price REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("📁 Datenbank & Tabelle wurden erfolgreich erstellt.")
    except sqlite3.DatabaseError as e:
        print(f"❌ Fehler bei der DB-Erstellung: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_database()

def save_price_to_db(coin: str, price: float):
    try:
        conn = sqlite3.connect("crypto.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO preise (coin, price)
            VALUES (?, ?)
        """, (coin, price))
        conn.commit()
        st.success(f"✅ Preis von {coin} wurde gespeichert!")
    except sqlite3.DatabaseError as e:
        st.error(f"Fehler beim Speichern in die Datenbank: {e}")
    finally:
        if conn:
            conn.close()

# Aufgabe 1 - Button erstellen
coin_input = st.text_input("🔎 Kryptowährung eingeben (z.B. bitcoin, ethereum):")

if st.button("Kurs abrufen"):
    price = get_price(coin_input.lower())
    if price is not None:
        save_price_to_db(coin_input.lower(), price)

# Aufgabe 4 - Daten anzeigen und visualisieren

def get_saved_prices():
    try:
        conn = sqlite3.connect("crypto.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM preise ORDER BY timestamp DESC")
        rows = cursor.fetchall()

        if not rows:
            st.info("Keine gespeicherten Preise gefunden.")
            return pd.DataFrame(columns=["id", "coin", "price", "timestamp"])

        df = pd.DataFrame(rows, columns=["id", "coin", "price", "timestamp"])
        return df
    except Exception as e:
        st.error(f"Fehler beim Abrufen der Daten: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

st.header("📊 Gespeicherte Kryptowährungen & Preise")
df = get_saved_prices()

if not df.empty:
    st.dataframe(df)

    st.subheader("💡 Preisvergleich als Balkendiagramm")
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X("coin:N", title="Kryptowährung"),
        y=alt.Y("price:Q", title="Preis in EUR"),
        tooltip=["coin", "price"]
    ).properties(
        width=600,
        height=400
    )
    st.altair_chart(chart, use_container_width=True)
else:
    st.warning("Noch keine Daten gespeichert.")

# Aufgabe 5 - Filtern nach Kryptowährungen

st.header("🔍 Preis für eine bestimmte Kryptowährung anzeigen")

# Hole die gespeicherten Daten
df = get_saved_prices()

if not df.empty:
    coin_list = df["coin"].unique().tolist()
    selected_coin = st.selectbox("Wähle eine Kryptowährung aus:", coin_list)

    # Filter anwenden
    filtered_df = df[df["coin"] == selected_coin]

    if not filtered_df.empty:
        st.subheader(f"📄 Daten für: {selected_coin}")
        st.dataframe(filtered_df)

        # Optional: Zeige Preis noch einmal hervor
        preis = filtered_df["price"].values[0]
        st.metric(label=f"Aktueller Preis ({selected_coin})", value=f"{preis} €")
    else:
        st.warning("Keine Daten für die gewählte Kryptowährung gefunden.")
else:
    st.info("Noch keine gespeicherten Kryptowährungen verfügbar.")


# Aufgabe 6 - Einträge löschen
def delete_entry_by_id(entry_id: int):
    try:
        conn = sqlite3.connect("crypto.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM preise WHERE id = ?", (entry_id,))
        data = cursor.fetchone()

        if data:
            cursor.execute("DELETE FROM preise WHERE id = ?", (entry_id,))
            conn.commit()
            st.success(f"✅ Eintrag mit ID {entry_id} wurde gelöscht!")
        else:
            st.warning(f"⚠️ Kein Eintrag mit ID {entry_id} gefunden.")

    except sqlite3.DatabaseError as e:
        st.error(f"Fehler beim Löschen: {e}")
    finally:
        if conn:
            conn.close()

st.header("🗑️ Eintrag löschen")

df = get_saved_prices()

if not df.empty:
    st.dataframe(df)

    delete_id = st.number_input("Gib die ID des zu löschenden Eintrags ein:", min_value=1, step=1)

    if st.button("Eintrag löschen"):
        delete_entry_by_id(int(delete_id))
        st.rerun()  # Seite neu laden, um Änderungen anzuzeigen
else:
    st.info("Keine Einträge zum Löschen vorhanden.")
