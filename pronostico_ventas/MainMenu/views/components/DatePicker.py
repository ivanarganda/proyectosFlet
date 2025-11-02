import datetime
import flet as ft

def init_date_picker(
    page,
    filtrar_dataset,
    fecha_inicio_val,
    fecha_fin_val,
    MIN_DATE,
    MAX_DATE,
    df,
    input_periodo=None
):
    """
    Inicializa los DatePickers automáticamente según el rango de fechas del DataFrame.
    Sincroniza automáticamente con `input_periodo` si se proporciona.
    Devuelve un diccionario con todos los controles y la diferencia en días.
    """
    type_ = ""

    if not input_periodo is None:
        type_ = "predict"

    # === Función auxiliar para mantener formato y sincronización ===
    def update_input_period():
        """Actualiza el input_periodo con el rango seleccionado y los días de diferencia."""
        if input_periodo:
            try:
                start = datetime.datetime.strptime(fecha_inicio_val.value, "%Y-%m-%d")
                end = datetime.datetime.strptime(fecha_fin_val.value, "%Y-%m-%d")
                diff_days = (end - start).days
                input_periodo.value = diff_days
            except Exception:
                input_periodo.value = f"{fecha_inicio_val.value} → {fecha_fin_val.value}"
            page.update()

    # === Cambiar fecha de inicio ===
    def on_inicio_change(e: ft.ControlEvent):
        if e.control.value:
            picked = e.control.value
            if isinstance(picked, datetime.date) and not isinstance(picked, datetime.datetime):
                picked = datetime.datetime.combine(picked, datetime.time.min)
            picked = max(MIN_DATE, min(picked, MAX_DATE))
            fecha_inicio_val.value = picked.strftime("%Y-%m-%d")
            update_input_period()
            if filtrar_dataset and type_=="":
                filtrar_dataset()
            page.update()

    # === Cambiar fecha de fin ===
    def on_fin_change(e: ft.ControlEvent):
        if e.control.value:
            picked = e.control.value
            if isinstance(picked, datetime.date) and not isinstance(picked, datetime.datetime):
                picked = datetime.datetime.combine(picked, datetime.time.min)
            picked = max(MIN_DATE, min(picked, MAX_DATE))
            if fecha_fin_val.value < fecha_inicio_val.value:
                fecha_fin_val.value = fecha_inicio_val
            fecha_fin_val.value = picked.strftime("%Y-%m-%d")
            update_input_period()
            if filtrar_dataset and type_=="":
                filtrar_dataset()
            page.update()

    # === Crear los pickers ===
    picker_inicio = ft.DatePicker(
        on_change=on_inicio_change,
        first_date=MIN_DATE,
        last_date=MAX_DATE if type_!="predict" else MIN_DATE,
        date_picker_entry_mode=ft.DatePickerEntryMode.CALENDAR_ONLY,
    )
    picker_fin = ft.DatePicker(
        on_change=on_fin_change,
        first_date=MIN_DATE,
        last_date=MAX_DATE,
        date_picker_entry_mode=ft.DatePickerEntryMode.CALENDAR_ONLY,
    )
    page.overlay.extend([picker_inicio, picker_fin])

    # === Botones ===
    btn_inicio = ft.ElevatedButton(
        "📅 From date",
        on_click=lambda e: picker_inicio.pick_date(),
        bgcolor="#5A2D9C",
        color="white",
    )
    btn_fin = ft.ElevatedButton(
        "📅 To date",
        on_click=lambda e: picker_fin.pick_date(),
        bgcolor="#5A2D9C",
        color="white",
    )

    # === Contenedor visual ===
    component = ft.Row(
        [
            ft.Column([btn_inicio, fecha_inicio_val]),
            ft.Column([btn_fin, fecha_fin_val]),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=25,
    )

    # === Sincronización inicial ===
    update_input_period()

    # === Calcular diferencia inicial ===
    try:
        start = datetime.datetime.strptime(fecha_inicio_val.value, "%Y-%m-%d")
        end = datetime.datetime.strptime(fecha_fin_val.value, "%Y-%m-%d")
        diff_days = (end - start).days
    except Exception:
        diff_days = 0

    # === Retornar todos los controles ===
    return {
        "component": component,
        "btn_inicio": btn_inicio,
        "btn_fin": btn_fin,
        "fecha_inicio_val": fecha_inicio_val,
        "fecha_fin_val": fecha_fin_val,
        "diff": {"days": diff_days},  # ✅ diferencia inicial de días
    }