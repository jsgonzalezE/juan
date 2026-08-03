# -*- coding: utf-8 -*-
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, HRFlowable, ListFlowable, ListItem, KeepTogether)

OUT = "/home/user/juan/Informe-Seguridad-burmancoffee.pdf"

# ---- Paleta (acento café) ----
COFFEE   = colors.HexColor("#5B3A29")
COFFEE2  = colors.HexColor("#8C6D5B")
INK      = colors.HexColor("#2B2B2B")
GREY     = colors.HexColor("#6B6B6B")
LIGHT    = colors.HexColor("#F3EEEA")
RED      = colors.HexColor("#C0392B")
ORANGE   = colors.HexColor("#E67E22")
AMBER    = colors.HexColor("#D4A017")
BLUE     = colors.HexColor("#2E77B5")
GREEN    = colors.HexColor("#2E8B57")
WHITE    = colors.white

SEV = {
    "Media":       ORANGE,
    "Baja":        AMBER,
    "Informativa": BLUE,
    "Alta":        RED,
}

styles = getSampleStyleSheet()
def S(name, **kw):
    styles.add(ParagraphStyle(name, **kw))

S("Cover",     fontName="Helvetica-Bold", fontSize=30, textColor=WHITE, leading=34)
S("CoverSub",  fontName="Helvetica",      fontSize=14, textColor=WHITE, leading=18)
S("CoverMeta", fontName="Helvetica",      fontSize=10.5, textColor=colors.HexColor("#EADFD7"), leading=16)
S("H1", fontName="Helvetica-Bold", fontSize=15, textColor=COFFEE, leading=19, spaceBefore=6, spaceAfter=8)
S("H2", fontName="Helvetica-Bold", fontSize=11.5, textColor=INK, leading=15, spaceBefore=8, spaceAfter=3)
S("Body", fontName="Helvetica", fontSize=9.7, textColor=INK, leading=14.5, alignment=TA_JUSTIFY, spaceAfter=5)
S("Small", fontName="Helvetica", fontSize=8.5, textColor=GREY, leading=12)
S("Cell", fontName="Helvetica", fontSize=8.7, textColor=INK, leading=12)
S("CellB", fontName="Helvetica-Bold", fontSize=8.7, textColor=INK, leading=12)
S("CellW", fontName="Helvetica-Bold", fontSize=8.7, textColor=WHITE, leading=12, alignment=TA_CENTER)
S("Badge", fontName="Helvetica-Bold", fontSize=8.5, textColor=WHITE, leading=11, alignment=TA_CENTER)
S("KPINum", fontName="Helvetica-Bold", fontSize=22, textColor=COFFEE, leading=24, alignment=TA_CENTER)
S("KPILbl", fontName="Helvetica", fontSize=8, textColor=GREY, leading=10, alignment=TA_CENTER)

def P(t, s="Body"): return Paragraph(t, styles[s])

# ---------------------------------------------------------------- page furniture
def header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    # header band
    canvas.setFillColor(COFFEE)
    canvas.rect(0, h-1.15*cm, w, 1.15*cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(1.6*cm, h-0.75*cm, "Evaluación de Seguridad — burmancoffee.com")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(w-1.6*cm, h-0.75*cm, "CONFIDENCIAL")
    # footer
    canvas.setStrokeColor(colors.HexColor("#DDD3CC"))
    canvas.setLineWidth(0.5)
    canvas.line(1.6*cm, 1.15*cm, w-1.6*cm, 1.15*cm)
    canvas.setFillColor(GREY)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(1.6*cm, 0.75*cm, "Informe generado el 3 de agosto de 2026 · Uso interno")
    canvas.drawRightString(w-1.6*cm, 0.75*cm, "Página %d" % doc.page)
    canvas.restoreState()

def cover(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(COFFEE)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#6E4A35"))
    canvas.rect(0, h-9.5*cm, w, 9.5*cm, fill=1, stroke=0)
    # coffee mark
    canvas.setFillColor(colors.HexColor("#EADFD7"))
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(1.8*cm, h-2.2*cm, "INFORME EJECUTIVO DE CIBERSEGURIDAD")
    canvas.setStrokeColor(colors.HexColor("#C8A98F"))
    canvas.setLineWidth(1)
    canvas.line(1.8*cm, h-2.55*cm, 8.2*cm, h-2.55*cm)
    canvas.restoreState()

# ---------------------------------------------------------------- helpers
def sev_badge(text):
    c = SEV.get(text, GREY)
    t = Table([[Paragraph(text, styles["Badge"])]], colWidths=[2.1*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), c),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),3), ("BOTTOMPADDING",(0,0),(-1,-1),3),
    ]))
    return t

story = []

# ================================================================ COVER
story += [Spacer(1, 5.7*cm)]
story += [P("Evaluación de Seguridad Web", "Cover")]
story += [Spacer(1, 0.2*cm)]
story += [P("burmancoffee.com", "CoverSub")]
story += [Spacer(1, 5.4*cm)]
story += [P("Sitio evaluado: &nbsp; https://burmancoffee.com", "CoverMeta")]
story += [P("Tipo de evaluación: &nbsp; Pasiva / no intrusiva (sin interrupción del servicio)", "CoverMeta")]
story += [P("Fecha: &nbsp; 3 de agosto de 2026", "CoverMeta")]
story += [P("Clasificación: &nbsp; Confidencial — uso interno", "CoverMeta")]
story += [PageBreak()]

# ================================================================ 1. RESUMEN EJECUTIVO
story += [P("1. Resumen ejecutivo", "H1")]
story += [P(
  "Se realizó una evaluación de seguridad del sitio web <b>burmancoffee.com</b> a partir de un "
  "escaneo externo (38 comprobaciones) complementado con análisis experto y verificación forense. "
  "El objetivo fue identificar puntos débiles, servicios expuestos y riesgos antes de que puedan ser "
  "aprovechados por un tercero.", "Body")]
story += [P(
  "<b>Veredicto general:</b> la base de seguridad del sitio es <b>sólida</b>. Está protegido por "
  "Cloudflare (firewall de aplicaciones web y CDN), usa cifrado moderno (TLS 1.3) y no presenta "
  "malware, vulnerabilidades críticas conocidas ni aparece en listas negras. <b>No se encontró una "
  "brecha crítica ni un acceso directo al sistema.</b> Sin embargo, se identificaron <b>9 puntos de "
  "mejora</b>, de los cuales <b>dos representan un riesgo real para el negocio</b> y conviene atender "
  "con prioridad.", "Body")]

# KPI row
kpi = Table([[
    Table([[P("0","KPINum")],[P("Críticos / Altos","KPILbl")]]),
    Table([[P('<font color="#E67E22">4</font>',"KPINum")],[P("Riesgo Medio","KPILbl")]]),
    Table([[P('<font color="#D4A017">3</font>',"KPINum")],[P("Riesgo Bajo","KPILbl")]]),
    Table([[P('<font color="#2E77B5">2</font>',"KPINum")],[P("Informativos","KPILbl")]]),
]], colWidths=[4.1*cm]*4)
kpi.setStyle(TableStyle([
    ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#DDD3CC")),
    ("INNERGRID",(0,0),(-1,-1),0.5,colors.HexColor("#DDD3CC")),
    ("BACKGROUND",(0,0),(-1,-1),LIGHT),
    ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),
]))
story += [Spacer(1,0.2*cm), kpi, Spacer(1,0.35*cm)]

story += [P("Los 3 asuntos que más importan al negocio", "H2")]
top3 = [
  ("① Es posible suplantar el correo de la empresa.",
   "La configuración anti-suplantación del correo (DMARC) está en modo “solo observar”. Un tercero "
   "puede enviar correos que aparentan venir de <b>@burmancoffee.com</b> (facturas falsas a clientes, "
   "fraude a proveedores/empleados) y llegarán a la bandeja de entrada."),
  ("② Existe un entorno de desarrollo expuesto en internet.",
   "Se detectó <b>dev.burmancoffee.com</b> visible públicamente. Estos entornos suelen estar menos "
   "protegidos y pueden revelar la dirección real del servidor, permitiendo a un atacante <b>rodear el "
   "firewall de Cloudflare</b>."),
  ("③ Una de las claves de firma del correo es débil.",
   "Se confirmó (criptográficamente) que una de las llaves DKIM es de 1024 bits, por debajo del "
   "estándar actual de 2048 bits."),
]
for t,d in top3:
    story += [P("<b>%s</b>" % t, "Body"), P(d, "Body")]

story += [PageBreak()]

# ================================================================ 2. ALCANCE Y METODOLOGÍA
story += [P("2. Alcance y metodología", "H1")]
story += [P(
  "<b>Objetivo:</b> el sitio público burmancoffee.com y su configuración de dominio, correo y "
  "transporte (TLS).", "Body")]
story += [P(
  "<b>Base del análisis:</b> informe de la herramienta de escaneo <i>Web-Check</i> (38 comprobaciones "
  "de DNS, TLS, cabeceras HTTP, correo, puertos y reputación), enriquecido con análisis manual "
  "experto y verificación forense de las claves de firma del correo.", "Body")]
story += [P(
  "<b>Naturaleza:</b> evaluación <b>pasiva y no intrusiva</b>. Equivale a observar el sitio como lo "
  "haría un visitante o una consulta pública; <b>no</b> se explotaron vulnerabilidades, <b>no</b> se "
  "envió tráfico de ataque y <b>no</b> se interrumpió el servicio en ningún momento.", "Body")]

note = Table([[P(
  "<b>Nota de transparencia.</b> El entorno usado para elaborar este informe no tenía salida a "
  "internet habilitada, por lo que las comprobaciones <i>en vivo</i> contra el servidor no se "
  "ejecutaron; el análisis se basa en el escaneo aportado más la revisión experta. Se entregó, "
  "además, un conjunto de <b>herramientas de verificación</b> (scripts) para confirmar cada hallazgo "
  "en vivo y para una fase posterior de pruebas activas con alcance acordado.", "Cell")]],
  colWidths=[17*cm])
note.setStyle(TableStyle([
  ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#FBF6EF")),
  ("BOX",(0,0),(-1,-1),0.6,COFFEE2),
  ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10),
  ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),
]))
story += [Spacer(1,0.1*cm), note, Spacer(1,0.3*cm)]

# ================================================================ 3. PUERTOS
story += [P("3. Puertos y servicios expuestos", "H1")]
story += [P("Un “puerto abierto” es una puerta de entrada a un servidor. Cuantas menos puertas "
            "innecesarias haya abiertas hacia internet, menor es la superficie de ataque.", "Body")]

story += [P("Puertos ABIERTOS", "H2")]
data = [
    [P("Puerto","CellW"), P("Servicio","CellW"), P("Estado","CellW"), P("Interpretación","CellW")],
    [P("80","Cell"),   P("HTTP","Cell"),     P("Abierto","CellB"), P("Web sin cifrar; redirige a HTTPS. Punto de entrada de Cloudflare.","Cell")],
    [P("443","Cell"),  P("HTTPS","Cell"),    P("Abierto","CellB"), P("Web cifrada (TLS 1.3). Punto de entrada de Cloudflare. Correcto.","Cell")],
    [P("8080","Cell"), P("HTTP alt.","Cell"),P("Abierto","CellB"), P("Puerto estándar del proxy de Cloudflare; termina en el borde de Cloudflare, no en el servidor de origen.","Cell")],
]
t = Table(data, colWidths=[1.6*cm, 2.2*cm, 1.9*cm, 11.3*cm])
t.setStyle(TableStyle([
    ("BACKGROUND",(0,0),(-1,0),COFFEE),
    ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LIGHT]),
    ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#DDD3CC")),
    ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
]))
story += [t, Spacer(1,0.25*cm)]

story += [P("Puertos CERRADOS hacia internet (esto es bueno)", "H2")]
story += [P("Los servicios sensibles <b>no están expuestos</b> directamente a internet, lo cual es "
            "correcto. Se confirmó que no respondían los siguientes puertos, entre otros:", "Body")]
closed = [
    [P("21 FTP","Cell"), P("22 SSH","Cell"), P("23 Telnet","Cell"), P("25 SMTP","Cell"), P("110 POP3","Cell"), P("143 IMAP","Cell")],
    [P("389 LDAP","Cell"), P("587 SMTP","Cell"), P("993 IMAPS","Cell"), P("995 POP3S","Cell"), P("3306 MySQL","Cell"), P("3389 RDP","Cell")],
    [P("5060 SIP","Cell"), P("5900 VNC","Cell"), P("8000 HTTP","Cell"), P("8888 HTTP","Cell"), P("3000 App","Cell"), P("161 SNMP","Cell")],
]
tc = Table(closed, colWidths=[2.83*cm]*6)
tc.setStyle(TableStyle([
    ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#E3DAD2")),
    ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F4F8F4")),
    ("TEXTCOLOR",(0,0),(-1,-1),colors.HexColor("#2E8B57")),
    ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
]))
story += [tc, Spacer(1,0.15*cm)]
story += [P("Conclusión de puertos: la superficie de red expuesta es <b>mínima y adecuada</b>. Las "
            "únicas puertas abiertas son las del servicio web a través de Cloudflare.", "Small")]

story += [PageBreak()]

# ================================================================ 4. RESUMEN DE HALLAZGOS
story += [P("4. Resumen de hallazgos", "H1")]
rows = [
  ["#","Hallazgo","Severidad","Riesgo para el negocio"],
  ["1","Correo suplantable (DMARC en modo solo-observación + SPF débil)","Media","Phishing/fraude a clientes y empleados en nombre de la empresa"],
  ["2","Entorno de desarrollo expuesto / posible IP de origen visible","Media","Un atacante podría rodear el firewall y atacar el servidor"],
  ["3","Falta la cabecera HSTS","Media","Riesgo de intercepción de la conexión en redes no confiables"],
  ["4","DNSSEC no habilitado","Media","Posible redirección del dominio por manipulación de DNS"],
  ["5","Clave de firma de correo (DKIM) de 1024 bits","Baja","Firma de correo por debajo del estándar actual"],
  ["6","Sin archivo security.txt","Baja","Sin canal claro para reportes de seguridad responsables"],
  ["7","OCSP stapling no presente","Baja","Menor rendimiento/privacidad en la validación del certificado"],
  ["8","Divulgación de servidor y cabeceras obsoletas","Informativa","Higiene técnica; impacto mínimo"],
  ["9","Puntuación SEO 40 (no es un asunto de seguridad)","Informativa","Visibilidad en buscadores, no seguridad"],
]
tbl = [[P(rows[0][0],"CellW"),P(rows[0][1],"CellW"),P(rows[0][2],"CellW"),P(rows[0][3],"CellW")]]
stylecmds = [
    ("BACKGROUND",(0,0),(-1,0),COFFEE),
    ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#DDD3CC")),
    ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
]
for i, r in enumerate(rows[1:], start=1):
    sev = r[2]
    tbl.append([P(r[0],"Cell"), P(r[1],"Cell"),
                Paragraph(sev, styles["Badge"]), P(r[3],"Cell")])
    stylecmds.append(("BACKGROUND",(2,i),(2,i), SEV[sev]))
    if i % 2 == 0:
        stylecmds.append(("BACKGROUND",(0,i),(1,i), LIGHT))
        stylecmds.append(("BACKGROUND",(3,i),(3,i), LIGHT))
T = Table(tbl, colWidths=[0.8*cm, 6.7*cm, 2.2*cm, 7.3*cm])
T.setStyle(TableStyle(stylecmds))
story += [T]

story += [PageBreak()]

# ================================================================ 5. DETALLE
story += [P("5. Detalle de los hallazgos principales", "H1")]
def finding(num, title, sev, que, riesgo, accion):
    block = []
    head = Table([[P("Hallazgo %s — %s" % (num, title), "CellB"), sev_badge(sev)]],
                 colWidths=[14.9*cm, 2.1*cm])
    head.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                              ("BACKGROUND",(0,0),(0,0),LIGHT),
                              ("LEFTPADDING",(0,0),(0,0),8),
                              ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    block += [head, Spacer(1,0.12*cm)]
    block += [P("<b>Qué es:</b> " + que, "Body")]
    block += [P("<b>Riesgo:</b> " + riesgo, "Body")]
    block += [P("<b>Recomendación:</b> " + accion, "Body")]
    block += [Spacer(1,0.25*cm)]
    return KeepTogether(block)

story += [finding("1","Correo suplantable","Media",
  "La política DMARC del dominio está en <b>p=none</b> (solo observa, no bloquea) y el registro SPF "
  "usa <b>~all</b> (permisivo). Juntos, no impiden que un tercero envíe correo aparentando ser de "
  "@burmancoffee.com.",
  "Un atacante puede enviar facturas o comunicaciones falsas a clientes, proveedores o empleados "
  "haciéndose pasar por la empresa (phishing y fraude del tipo “Business Email Compromise”). Es el "
  "hallazgo con mayor impacto directo de negocio.",
  "Endurecer DMARC por fases: de p=none a <b>p=quarantine</b> y finalmente <b>p=reject</b>, revisando "
  "los informes para no afectar el correo legítimo. Ajustar SPF a <b>-all</b> cuando esté verificado.")]

story += [finding("2","Entorno de desarrollo expuesto / posible IP de origen","Media",
  "Se detectaron los subdominios <b>dev.burmancoffee.com</b> y <b>www.dev.burmancoffee.com</b> "
  "públicamente visibles (vía registros de transparencia de certificados).",
  "Los entornos de desarrollo suelen estar menos protegidos (sin firewall, con datos de prueba o "
  "credenciales por defecto) y pueden filtrar la dirección real del servidor. Si eso ocurre, un "
  "atacante puede <b>rodear por completo el firewall de Cloudflare</b> y atacar el servidor directo.",
  "Proteger dev con inicio de sesión (Cloudflare Access) o restringirlo por IP/VPN; asegurar que pasa "
  "por Cloudflare y no revela la IP de origen; verificar que no exponga paneles, código ni copias de "
  "seguridad.")]

story += [finding("3","Falta la cabecera HSTS","Media",
  "El sitio no envía la cabecera <b>Strict-Transport-Security</b>, que obliga al navegador a usar "
  "siempre HTTPS.",
  "En una red no confiable (Wi-Fi público), un atacante podría intentar degradar la conexión a HTTP "
  "sin cifrar e interceptar datos o sesiones.",
  "Activar HSTS en Cloudflare (empezar con 6 meses y luego 1 año), verificando antes que todos los "
  "subdominios funcionan por HTTPS.")]

story += [finding("4","DNSSEC no habilitado","Media",
  "El dominio no está firmado con DNSSEC; las respuestas DNS no tienen verificación criptográfica.",
  "Facilita ataques de manipulación de DNS que podrían redirigir la web o el correo del dominio hacia "
  "servidores maliciosos.",
  "Activar DNSSEC en Cloudflare (un clic) y publicar el registro DS correspondiente en el registrador "
  "(Register.com).")]

story += [finding("5","Clave de firma de correo (DKIM) de 1024 bits","Baja",
  "Verificado criptográficamente: de las tres claves DKIM publicadas, dos son de 2048 bits (correcto) "
  "y una es de <b>1024 bits</b> (nivel legado).",
  "Una clave de 1024 bits ofrece menor garantía de autenticidad del correo firmado con ese selector.",
  "Rotar esa clave a 2048 bits o eliminar el selector si ya no se utiliza.")]

story += [PageBreak()]

# ================================================================ 6. FORTALEZAS
story += [P("6. Lo que está correctamente protegido", "H1")]
story += [P("Para dar contexto equilibrado, el sitio ya hace bien muchas cosas importantes:", "Body")]
strengths = [
  "Protegido por <b>Cloudflare</b> (firewall de aplicaciones web + CDN), que ya bloqueó al escáner con un desafío de seguridad.",
  "Cifrado moderno <b>TLS 1.3</b> con confidencialidad hacia el futuro (forward secrecy).",
  "Certificado SSL válido y de confianza, vigente hasta octubre de 2026.",
  "Protección de correo básica presente: <b>SPF</b> y <b>DKIM</b> configurados (Google Workspace).",
  "<b>Sin malware, sin phishing</b> y sin coincidencias en listas negras ni feeds de amenazas.",
  "Sin vulnerabilidades críticas conocidas en la tecnología detectada.",
  "Superficie de red mínima: los servicios sensibles (SSH, RDP, bases de datos) no están expuestos.",
  "Dominio consolidado (registrado desde 2002) y con buenas puntuaciones de rendimiento y accesibilidad.",
]
story += [ListFlowable([ListItem(P(s,"Body"), leftIndent=6) for s in strengths],
                       bulletType="bullet", start="•", bulletColor=GREEN)]

# ================================================================ 7. PLAN DE ACCIÓN
story += [Spacer(1,0.2*cm), P("7. Plan de acción priorizado", "H1")]
plan = [
  ["Prioridad","Acción","Esfuerzo"],
  ["1 · Alta","Endurecer DMARC (p=none → quarantine → reject) para frenar la suplantación de correo","Bajo"],
  ["2 · Alta","Revisar y proteger dev.burmancoffee.com; confirmar que no filtra la IP de origen","Medio"],
  ["3 · Media","Activar HSTS en Cloudflare","Muy bajo"],
  ["4 · Media","Habilitar DNSSEC (Cloudflare + Register.com)","Bajo"],
  ["5 · Baja","Rotar la clave DKIM de 1024 → 2048 bits","Bajo"],
  ["6 · Baja","Publicar security.txt y retirar cabeceras obsoletas","Muy bajo"],
]
pt = [[P(plan[0][0],"CellW"),P(plan[0][1],"CellW"),P(plan[0][2],"CellW")]]
for r in plan[1:]:
    pt.append([P(r[0],"CellB"),P(r[1],"Cell"),P(r[2],"Cell")])
PT = Table(pt, colWidths=[2.7*cm, 11.6*cm, 2.7*cm])
PT.setStyle(TableStyle([
    ("BACKGROUND",(0,0),(-1,0),COFFEE),
    ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LIGHT]),
    ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#DDD3CC")),
    ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
]))
story += [PT]

# ================================================================ 8. CONCLUSIÓN
story += [Spacer(1,0.3*cm), P("8. Conclusión y próximos pasos", "H1")]
story += [P(
  "El sitio burmancoffee.com parte de una <b>buena base de seguridad</b> y no presenta una brecha "
  "crítica. Los hallazgos son mayoritariamente de <b>endurecimiento</b>, pero dos de ellos —la "
  "posibilidad de <b>suplantar el correo de la empresa</b> y la <b>exposición del entorno de "
  "desarrollo</b>— conllevan riesgo real de negocio y deben priorizarse. Todas las correcciones son "
  "abordables y de esfuerzo bajo o medio.", "Body")]
story += [P(
  "<b>Próximo paso recomendado:</b> ejecutar la verificación <i>en vivo</i> con las herramientas "
  "entregadas (búsqueda de IP de origen y batería de comprobaciones) desde un entorno con acceso a "
  "internet, y planificar una fase de <b>pruebas activas con alcance acordado</b> contra un entorno de "
  "pruebas para validar la lógica de la tienda y el proceso de compra.", "Body")]

story += [Spacer(1,0.3*cm), HRFlowable(width="100%", color=colors.HexColor("#DDD3CC"))]
story += [P("Documento confidencial preparado para uso interno. Los hallazgos reflejan el estado "
            "observado a la fecha del informe y deben re-verificarse tras aplicar los cambios.", "Small")]

# ---------------------------------------------------------------- build
doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=1.6*cm, rightMargin=1.6*cm,
                        topMargin=1.55*cm, bottomMargin=1.5*cm,
                        title="Evaluacion de Seguridad - burmancoffee.com",
                        author="Equipo de Seguridad")
doc.build(story, onFirstPage=cover, onLaterPages=header_footer)
print("PDF generado:", OUT)
