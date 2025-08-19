import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = "8073913728:AAGrwgMT-FJJ63gQOxgO7c3Xes6LYb_51fI"
ADMIN_ID = "TU_TELEGRAM_ID_AQUI"
# ⚠️ ¡IMPORTANTE! Reemplaza con la URL real de tu webhook de Make.
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/ta9x1i4xq5iod1te5rytqrgs0gmkzyw1" 

PRODUCTS = {
    1: {"name": "Guitarra", "price": 150, "image": "https://preview.free3d.com/img/2019/02/2206076674267678443/ax4u9gs8.jpg"},
    2: {"name": "Batería", "price": 500, "image": "https://th.bing.com/th/id/R.d6cbb7ff0130ece23b2f7b39e3d9a006?rik=jgVnjQHJ99qEng&pid=ImgRaw&r=0"},
    3: {"name": "Teclado", "price": 300, "image": "https://www.soundhouse.co.jp/contents/uploads/thumbs/2/2020/11/20201104_2_11511_1.jpg"},
    4: {"name": "Micrófono", "price": 100, "image": "https://i.imgur.com/KfJ2M2B.jpg"},
    5: {"name": "Violín", "price": 200, "image": "https://i.imgur.com/N6mL2Bd.jpg"},
}

CARTS = {}
PENDING_EMAIL = {} 

# --- Funciones principales ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "🎶 Bienvenido a *Instrument Golden*!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎸 Ver instrumentos", callback_data="show_products")],
                [InlineKeyboardButton("🛒 Ver carrito", callback_data="show_cart")],
                [InlineKeyboardButton("❌ Vaciar carrito", callback_data="clear_cart")]
            ]),
            parse_mode="Markdown"
        )
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "🎶 Bienvenido a *Instrument Golden*!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎸 Ver instrumentos", callback_data="show_products")],
                [InlineKeyboardButton("🛒 Ver carrito", callback_data="show_cart")],
                [InlineKeyboardButton("❌ Vaciar carrito", callback_data="clear_cart")]
            ]),
            parse_mode="Markdown"
        )

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(f"{p['name']} - ${p['price']}", callback_data=f"add_{pid}")]
                for pid, p in PRODUCTS.items()]
    keyboard.append([InlineKeyboardButton("⬅ Volver al menú", callback_data="menu")])
    await query.edit_message_text("🎸 Instrumentos disponibles:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    cart = CARTS.get(user_id, {})
    if not cart:
        await query.edit_message_text("🛒 Tu carrito está vacío.")
        return
    text = "🛍 Tu carrito:\n\n"
    keyboard = []
    total = 0
    for pid, qty in cart.items():
        product = PRODUCTS[pid]
        text += f"- {product['name']} (${product['price']} x {qty}) = ${product['price']*qty}\n"
        total += product['price'] * qty
        keyboard.append([InlineKeyboardButton("➖", callback_data=f"dec_{pid}"),
                         InlineKeyboardButton(f"{product['name']} ({qty})", callback_data="noop"),
                         InlineKeyboardButton("➕", callback_data=f"inc_{pid}")])
    text += f"\n💰 Total: ${total}"
    keyboard.append([InlineKeyboardButton("✅ Comprar todo", callback_data="checkout")])
    keyboard.append([InlineKeyboardButton("⬅ Volver al menú", callback_data="menu")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# --- Manejo de botones ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("add_"):
        pid = int(data.split("_")[1])
        product = PRODUCTS[pid]
        
        # Se asegura de que el carrito no esté en otro estado
        if user_id not in CARTS:
            CARTS[user_id] = {}
        
        cart = CARTS[user_id]
        cart[pid] = cart.get(pid, 0) + 1
        CARTS[user_id] = cart
        
        keyboard = [
            [InlineKeyboardButton("✅ Comprar", callback_data=f"confirm_{pid}")],
            [InlineKeyboardButton("⬅ Volver al menú", callback_data="menu")]
        ]
        await query.message.reply_photo(
            photo=product["image"],
            caption=f"🎸 {product['name']}\nPrecio: ${product['price']}\n\n¿Desea comprar este instrumento?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    elif data.startswith("confirm_"):
        pid = int(data.split("_")[1])
        # Lógica de confirmación de compra y solicitud de correo
        cart = CARTS.get(user_id, {})
        if not cart:
            cart[pid] = 1 # Añade el producto si el carrito está vacío
        
        PENDING_EMAIL[user_id] = {"cart": cart.copy()}
        await query.message.reply_text(
            "🎉 ¡Compra exitosa! Por favor, ingresa tu correo electrónico para recibir la factura:"
        )
        return

    elif data == "menu":
        await start(update, context)
        return

    elif data == "checkout":
        cart = CARTS.get(user_id, {})
        if not cart:
            await query.edit_message_text("🛒 Tu carrito está vacío.")
            return
        PENDING_EMAIL[user_id] = {"cart": cart.copy()}
        await query.edit_message_text("📧 Ingresa tu correo electrónico para recibir la factura:")
        return

    elif data.startswith("inc_"):
        pid = int(data.split("_")[1])
        cart = CARTS.get(user_id, {})
        cart[pid] = cart.get(pid, 0) + 1
        CARTS[user_id] = cart
        await show_cart(update, context)
        
    elif data.startswith("dec_"):
        pid = int(data.split("_")[1])
        cart = CARTS.get(user_id, {})
        if pid in cart:
            cart[pid] -= 1
            if cart[pid] <= 0:
                del cart[pid]
            CARTS[user_id] = cart
        await show_cart(update, context)
        
    elif data == "clear_cart":
        CARTS.pop(user_id, None)
        await query.edit_message_text("❌ Carrito vaciado.")
        
    elif data == "noop":
        pass
        
    elif data == "show_products":
        await show_products(update, context)
        
    elif data == "show_cart":
        await show_cart(update, context)

# --- Admin ---
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.from_user.id) != ADMIN_ID:
        await update.message.reply_text("⛔ No tienes permisos de administrador.")
        return
    await update.message.reply_text("🔧 Panel de administrador:\nUsa /add <nombre> <precio> para agregar productos.")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.from_user.id) != ADMIN_ID:
        await update.message.reply_text("⛔ No tienes permisos de administrador.")
        return
    try:
        name = context.args[0]
        price = float(context.args[1])
        pid = max(PRODUCTS.keys()) + 1
        PRODUCTS[pid] = {"name": name, "price": price, "image": "https://i.imgur.com/placeholder.jpg"}
        await update.message.reply_text(f"✅ Producto agregado: {name} (${price})")
    except Exception:
        await update.message.reply_text("⚠️ Uso: /add <nombre> <precio>")

# --- Recibir correo y enviar a Make ---
async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in PENDING_EMAIL or "cart" not in PENDING_EMAIL[user_id]:
        return

    email = update.message.text
    cart = PENDING_EMAIL[user_id]["cart"]
    
    # Preparar los datos para Make
    total = sum(PRODUCTS[pid]['price'] * qty for pid, qty in cart.items())
    items_list = []
    for pid, qty in cart.items():
        product = PRODUCTS[pid]
        items_list.append({
            "name": product['name'],
            "price": product['price'],
            "quantity": qty,
            "subtotal": product['price'] * qty
        })
    
    data_to_send = {
        "email": email,
        "items": items_list,
        "total": total,
        "username": update.message.from_user.full_name,
        "message": "¡Tu compra fue realizada con exito! Gracias por tu pedido."
    }

    try:
        response = requests.post(MAKE_WEBHOOK_URL, json=data_to_send)
        response.raise_for_status()  # Lanza una excepción si la solicitud no fue exitosa
        await update.message.reply_text(f"🎉 ¡Factura enviada a {email}! Revisa tu correo.")
        CARTS.pop(user_id, None)
        PENDING_EMAIL.pop(user_id, None)
    except requests.exceptions.RequestException as e:
        await update.message.reply_text("⚠️ Ocurrió un error al enviar la factura. Por favor, revisa que la URL de Make esté correcta.")
        print(f"Error al enviar a Make: {e}")

# --- Main ---
def main():
    if not BOT_TOKEN:
        raise SystemExit("❌ Error: No se ha configurado el BOT_TOKEN de Telegram.")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email))
    print("✅ Bot iniciado... esperando mensajes en Telegram.")
    app.run_polling()

if __name__ == "__main__":
    main()
