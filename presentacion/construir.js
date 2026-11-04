// Genera parcial3.pptx (9 diapositivas, 7 a 10 minutos). Uso: node construir.js
const pptxgen = require("pptxgenjs");
const path = require("path");

const IMG = path.join(__dirname, "..", "docs", "img");
const NAVY = "1F2933", INK = "1F2933", MUTED = "52606D", PAPER = "FFFFFF", SOFT = "F0F4F8";
const ORANGE = "D55E00", BLUE = "0072B2", GREEN = "009E73";
const HEAD = "Cambria", BODY = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 pulgadas
pres.title = "Parcial 3: de rápido a verificable";
pres.author = "Octavio Briguera y Ricardo Lagoria";
pres.theme = { headFontFace: HEAD, bodyFontFace: BODY };

const shadow = () => ({ type: "outer", color: "000000", opacity: 0.12, blur: 6, offset: 2, angle: 90 });

function contenido(titulo, notas) {
  const s = pres.addSlide();
  s.background = { color: PAPER };
  s.addText(titulo, { x: 0.5, y: 0.3, w: 9, h: 0.7, fontFace: HEAD, fontSize: 30, bold: true, color: INK, margin: 0, isTextBox: true, valign: "middle" });
  s.addNotes(notas);
  return s;
}

function tarjeta(s, x, y, w, h, fill) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: fill || SOFT }, rectRadius: 0.08, line: { color: fill || SOFT, width: 0 }, shadow: shadow() });
}

function cifra(s, x, y, w, grande, chica, color) {
  tarjeta(s, x, y, w, 1.05);
  s.addText(grande, { x: x + 0.1, y: y + 0.08, w: w - 0.2, h: 0.55, fontFace: HEAD, fontSize: grande.length > 8 ? 20 : 26, bold: true, color, align: "center", margin: 0, isTextBox: true });
  s.addText(chica, { x: x + 0.1, y: y + 0.62, w: w - 0.2, h: 0.36, fontFace: BODY, fontSize: 12, color: MUTED, align: "center", margin: 0, isTextBox: true, valign: "top" });
}

function lista(s, items, x, y, w, h, size) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6 } })),
    { x, y, w, h, fontFace: BODY, fontSize: size || 14, color: INK, margin: 0, valign: "top", isTextBox: true });
}

// ---------------------------------------------------------------- 1 portada
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addText("Parcial 3: de rápido a verificable", { x: 0.7, y: 1.3, w: 8.6, h: 1.1, fontFace: HEAD, fontSize: 40, bold: true, color: "FFFFFF", margin: 0, isTextBox: true });
  s.addText("Motor de recomendación de películas por filtrado colaborativo", { x: 0.7, y: 2.45, w: 8.6, h: 0.5, fontFace: BODY, fontSize: 20, color: "CBD2D9", margin: 0, isTextBox: true });
  [["Base", ORANGE], ["Eficiente", BLUE], ["Optimizada", GREEN]].forEach(([nombre, color], i) => {
    const x = 0.7 + i * 1.9;
    s.addShape(pres.ShapeType.ellipse, { x, y: 3.35, w: 0.3, h: 0.3, fill: { color }, line: { color, width: 0 } });
    s.addText(nombre, { x: x + 0.4, y: 3.3, w: 1.4, h: 0.4, fontFace: BODY, fontSize: 16, color: "FFFFFF", margin: 0, isTextBox: true, valign: "middle" });
  });
  s.addText("Octavio Briguera · Ricardo Lagoria", { x: 0.7, y: 4.4, w: 8.6, h: 0.4, fontFace: BODY, fontSize: 16, bold: true, color: "FFFFFF", margin: 0, isTextBox: true });
  s.addText("Programación Eficiente · Universidad Blas Pascal", { x: 0.7, y: 4.8, w: 8.6, h: 0.4, fontFace: BODY, fontSize: 14, color: "CBD2D9", margin: 0, isTextBox: true });
  s.addNotes("[Ricardo, 10 s] Hola. Les contamos las novedades del Parcial 3. La idea en una frase: en el Parcial 2 dejamos un sistema rápido; en el 3 lo volvimos verificable, es decir, que cada cambio pasa por controles automáticos y se puede demostrar que no se rompió ni se enlenteció.");
}

// ---------------------------------------------------------------- 2 punto de partida
{
  const s = contenido("De dónde partimos",
    "[Ricardo, 1 min] El Parcial 2 terminó con una versión Optimizada rápida, pero sin red de seguridad: cobertura de 70,7 %, cuatro funciones que Xenon calificaba en rango B, seis errores de mypy y 33 hallazgos de Ruff. No había CI, ni política de seguridad, ni documentación publicada.\n\nTrabajamos en siete fases, una por pull request, con el CI corriendo en cada PR, y etiquetamos cada fase con un tag (parcial3-fase0 a fase6) para poder volver a cualquier punto. La Fase 6 no la pide el enunciado: la agregamos nosotros para medir cuánto mejoró la eficiencia entre las tres versiones.");
  cifra(s, 0.5, 1.3, 2.05, "70,7 %", "cobertura de tests", ORANGE);
  cifra(s, 2.75, 1.3, 2.05, "4", "funciones en rango B", ORANGE);
  cifra(s, 5.0, 1.3, 2.05, "6", "errores de mypy", ORANGE);
  cifra(s, 7.25, 1.3, 2.25, "33", "hallazgos de Ruff", ORANGE);
  s.addText("Siete fases, un pull request por fase", { x: 0.5, y: 2.75, w: 9, h: 0.4, fontFace: HEAD, fontSize: 18, bold: true, color: INK, margin: 0, isTextBox: true });
  const fases = ["Base reproducible", "Calidad", "Rendimiento", "Seguridad", "CI", "Documentación", "Evolución"];
  fases.forEach((nombre, i) => {
    const x = 0.5 + i * 1.3;
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.35, y: 3.3, w: 0.5, h: 0.5, fill: { color: i === 6 ? GREEN : BLUE }, line: { color: i === 6 ? GREEN : BLUE, width: 0 } });
    s.addText(String(i), { x: x + 0.35, y: 3.3, w: 0.5, h: 0.5, fontFace: HEAD, fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText(nombre, { x, y: 3.9, w: 1.2, h: 0.5, fontFace: BODY, fontSize: 12, color: INK, align: "center", valign: "top", margin: 0, isTextBox: true });
  });
  s.addText("Cada fase termina con un tag (parcial3-fase0 a fase6). La Fase 6 es un agregado propio: no figura en el enunciado.", { x: 0.5, y: 4.65, w: 9, h: 0.5, fontFace: BODY, fontSize: 13, italic: true, color: MUTED, margin: 0, isTextBox: true });
}

// ---------------------------------------------------------------- 3 fases 0 y 1
{
  const s = contenido("Fases 0 y 1: calidad verificable",
    "[Octavio, 1 min] Fase 0: dejamos el entorno reproducible. Las dependencias están bloqueadas con hashes y se instalan verificándolos; toda la configuración de las herramientas vive en pyproject.toml; y tasks.py es un runner que ejecuta exactamente los mismos comandos en la máquina local y en el CI. Lo que falla en el CI se reproduce con el mismo comando.\n\nFase 1: antes de tocar el código escribimos pruebas de caracterización (golden master) que comparan la salida del recomendador por igualdad exacta, sin tolerancia, contra el comportamiento previo. Con esa red, refactorizamos: todas las funciones pasaron al rango A de Xenon, con complejidad máxima 5; la cobertura subió de 70,7 a 100 %; mypy y Ruff quedaron en cero. Aprendizaje: un refactor limpio puede ser más lento, por eso medimos después de cada uno.");
  tarjeta(s, 0.5, 1.2, 4.35, 1.95);
  s.addText("Fase 0 · Base reproducible", { x: 0.7, y: 1.3, w: 4, h: 0.4, fontFace: HEAD, fontSize: 16, bold: true, color: BLUE, margin: 0, isTextBox: true });
  lista(s, ["Dependencias bloqueadas con hashes", "Configuración única en pyproject.toml", "tasks.py: los mismos comandos en local y en CI"], 0.7, 1.75, 4, 1.35, 14);
  tarjeta(s, 5.15, 1.2, 4.35, 1.95);
  s.addText("Fase 1 · Calidad sin romper nada", { x: 5.35, y: 1.3, w: 4, h: 0.4, fontFace: HEAD, fontSize: 16, bold: true, color: GREEN, margin: 0, isTextBox: true });
  lista(s, ["Primero tests de caracterización (golden master, igualdad exacta)", "Después el refactor, con Xenon, Ruff y mypy"], 5.35, 1.75, 4, 1.35, 14);
  cifra(s, 0.5, 3.45, 2.05, "70,7 → 100 %", "cobertura", GREEN);
  cifra(s, 2.75, 3.45, 2.05, "B → A", "complejidad (máxima: 5)", GREEN);
  cifra(s, 5.0, 3.45, 2.05, "6 → 0", "errores de mypy", GREEN);
  cifra(s, 7.25, 3.45, 2.25, "33 → 0", "hallazgos de Ruff", GREEN);
}

// ---------------------------------------------------------------- 4 fase 2
{
  const s = contenido("Fase 2: rendimiento y memoria",
    "[Ricardo, 1 min] En esta fase medimos antes de optimizar. Dos resultados concretos. Primero, recommend_movies con 40 usuarios sobre una matriz de 400 por 300 bajó de 447 a 198 milisegundos, 2,2 veces más rápido. Segundo, el procesamiento paralelo de archivos grandes: un test con tracemalloc detectó que la memoria crecía con el tamaño del archivo; con back-pressure (como máximo dos veces la cantidad de procesos en vuelo) el pico bajó de 67 a unos 9,3 MB y ya no crece.\n\nTambién definimos cómo se controla: los benchmarks comparan el mínimo contra una base con un umbral de 25 %, intercalando las corridas, porque medimos ruido de hasta 28 % entre corridas idénticas. Y la memoria se controla con un test relativo, que no depende de la máquina.");
  const colores = [ORANGE, GREEN];
  const grafico = (x, titulo, datos, unidad, formato) => {
    s.addText(titulo, { x, y: 1.2, w: 4.3, h: 0.55, fontFace: BODY, fontSize: 14, bold: true, color: INK, margin: 0, isTextBox: true, valign: "top" });
    s.addChart(pres.charts.BAR, [{ name: unidad, labels: ["Parcial 2", "Parcial 3"], values: datos }], {
      x, y: 1.8, w: 4.3, h: 2.3, barDir: "col", chartColors: colores, invertedColors: colores,
      showLegend: false, showTitle: false, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: formato, dataLabelFontSize: 14, dataLabelFontBold: true, dataLabelFontFace: BODY,
      catAxisLabelColor: INK, catAxisLabelFontSize: 13, catAxisLabelFontFace: BODY, valAxisHidden: true,
      valGridLine: { style: "none" }, catGridLine: { style: "none" }, valAxisMinVal: 0,
    });
  };
  grafico(0.5, "recommend_movies, 40 usuarios (ms)", [447, 198], "ms", "0");
  grafico(5.2, "Pico de memoria del procesamiento paralelo (MB)", [67, 9.3], "MB", "0.0");
  s.addText("2,2 × más rápido", { x: 0.5, y: 4.2, w: 4.3, h: 0.35, fontFace: HEAD, fontSize: 18, bold: true, color: GREEN, align: "center", margin: 0, isTextBox: true });
  s.addText("ya no crece con el archivo", { x: 5.2, y: 4.2, w: 4.3, h: 0.35, fontFace: HEAD, fontSize: 18, bold: true, color: GREEN, align: "center", margin: 0, isTextBox: true });
  s.addText("Los benchmarks comparan el mínimo con un umbral de 25 %; la memoria, con un test relativo que no depende de la máquina.", { x: 0.5, y: 4.75, w: 9, h: 0.5, fontFace: BODY, fontSize: 13, italic: true, color: MUTED, margin: 0, isTextBox: true });
}

// ---------------------------------------------------------------- 5 fases 3 y 4
{
  const s = contenido("Fases 3 y 4: seguridad y CI",
    "[Octavio, 1 min] Seguridad: hay una política (SECURITY.md) y cada control está verificado con un caso positivo, para saber que la herramienta realmente detecta algo. Bandit analiza el código, pip-audit las dependencias (las excepciones llevan motivo y vencimiento, y una vencida hace fallar la auditoría), Gitleaks los secretos en el historial y CodeQL el análisis semántico. Además se validan las entradas de la API.\n\nIntegración continua: GitHub Actions corre en cada push a master y en cada pull request hacia master. Las pruebas corren en Python 3.11, 3.12 y 3.13. Las acciones están fijadas por SHA de commit y el runner por versión, ubuntu-24.04, para que un cambio externo no rompa el CI sin que nadie lo toque. Todo converge en un único check, Resultado, que está exigido en la protección de master: sin él en verde, no se mergea. Las mediciones más costosas, como el perfilado, van al final.");
  tarjeta(s, 0.5, 1.2, 4.35, 2.05);
  s.addText("Seguridad", { x: 0.7, y: 1.3, w: 4, h: 0.4, fontFace: HEAD, fontSize: 16, bold: true, color: ORANGE, margin: 0, isTextBox: true });
  lista(s, ["SECURITY.md y registro de excepciones", "Bandit, pip-audit, Gitleaks y CodeQL", "Excepciones con motivo y vencimiento", "Validación de entradas de la API"], 0.7, 1.75, 4, 1.45, 14);
  tarjeta(s, 5.15, 1.2, 4.35, 2.05);
  s.addText("Integración continua", { x: 5.35, y: 1.3, w: 4, h: 0.4, fontFace: HEAD, fontSize: 16, bold: true, color: BLUE, margin: 0, isTextBox: true });
  lista(s, ["En cada push y PR hacia master", "Python 3.11, 3.12 y 3.13", "Acciones fijadas por SHA de commit", "Un solo check exigido: Resultado"], 5.35, 1.75, 4, 1.45, 14);
  const pasos = ["Calidad", "Secretos", "Pruebas", "Dependencias", "Docs", "Benchmarks", "Perfilado"];
  pasos.forEach((p, i) => {
    const x = 0.5 + i * 1.07;
    s.addShape(pres.ShapeType.roundRect, { x, y: 3.7, w: 0.98, h: 0.55, fill: { color: i >= 5 ? MUTED : BLUE }, rectRadius: 0.06, line: { color: i >= 5 ? MUTED : BLUE, width: 0 } });
    s.addText(p, { x, y: 3.7, w: 0.98, h: 0.55, fontFace: BODY, fontSize: 11, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
  });
  s.addShape(pres.ShapeType.roundRect, { x: 0.5, y: 4.4, w: 8.98, h: 0.5, fill: { color: GREEN }, rectRadius: 0.06, line: { color: GREEN, width: 0 } });
  s.addText("Resultado: el único check que exige la protección de master", { x: 0.5, y: 4.4, w: 8.98, h: 0.5, fontFace: BODY, fontSize: 14, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
  s.addText("Lo más costoso (benchmarks y perfilado) va al final del pipeline.", { x: 0.5, y: 5.0, w: 9, h: 0.3, fontFace: BODY, fontSize: 12, italic: true, color: MUTED, margin: 0, isTextBox: true });
}

// ---------------------------------------------------------------- 6 fase 5 y enunciado
{
  const s = contenido("Fase 5: documentación y enunciado",
    "[Ricardo, 1 min] La documentación técnica se construye con MkDocs Material, con la referencia del código generada desde los docstrings, y se publica en GitHub Pages al hacer merge en master. Sphinx se mantiene en paralelo. El build falla ante cualquier advertencia, y se validan los enlaces: los internos y anclas en cada build, y los externos con una tarea propia.\n\nAl incorporar el PDF del enunciado hicimos una auditoría requisito por requisito y cerramos tres brechas: el tamaño de las funciones, la validez de enlaces externos y el orden del pipeline. Lo que ven acá es lo cubierto con evidencia: las nueve secciones de documentación, las once filas de la matriz de controles, los seis requisitos de seguridad, las nueve condiciones de rechazo, y que los benchmarks y la memoria usen criterios distintos, como pide el enunciado.");
  const items = [["9", "secciones de documentación publicadas", BLUE], ["11", "filas de la matriz de controles", BLUE], ["6", "requisitos de seguridad", ORANGE],
    ["9", "condiciones de rechazo", ORANGE], ["Internos y externos", "enlaces validados en cada build", GREEN], ["3 criterios", "tolerancia, repetición y línea base", GREEN]];
  items.forEach(([g, c, color], i) => {
    const x = 0.5 + (i % 3) * 3.05, y = 1.3 + Math.floor(i / 3) * 1.45;
    tarjeta(s, x, y, 2.85, 1.25);
    s.addText(g, { x: x + 0.1, y: y + 0.12, w: 2.65, h: 0.6, fontFace: HEAD, fontSize: g.length > 3 ? 20 : 30, bold: true, color, align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText(c, { x: x + 0.1, y: y + 0.75, w: 2.65, h: 0.42, fontFace: BODY, fontSize: 12, color: MUTED, align: "center", valign: "top", margin: 0, isTextBox: true });
  });
  s.addText("Auditoría contra el enunciado: cada requisito tiene su evidencia. Sitio publicado con GitHub Pages.", { x: 0.5, y: 4.4, w: 9, h: 0.5, fontFace: BODY, fontSize: 14, italic: true, color: MUTED, margin: 0, isTextBox: true });
}

// ---------------------------------------------------------------- 7 fase 6
{
  const s = contenido("Fase 6: evolución de la eficiencia",
    "[Octavio, 1,5 min] Esta fase es un agregado nuestro: queríamos ver cuánto mejoró cada entrega. Usamos el mismo dataset con semilla fija para las tres versiones, cada una en un proceso aparte, con 250 a 2.000 usuarios. Además, la medición falla si las tres versiones no recomiendan lo mismo.\n\nResultado: con 2.000 usuarios Base tarda 33 segundos y Optimizada 94 milisegundos, unas 350 veces menos. Casi todo viene de la similitud entre usuarios, 818 veces, por pasar de pares de diccionarios a una multiplicación de matrices float32 en BLAS.\n\nSALVEDAD, y es un hallazgo real: en este banco la versión Eficiente no supera a la Base en la similitud; con 1.000 y 2.000 usuarios es más lenta, 0,75 veces. La explicación: armar dos sets por cada par de usuarios cuesta más que recorrer 30 elementos con un in sobre un diccionario, y hay cuatro millones de pares. Mejora donde el costo de armar los sets no pesa, como la popularidad (1,6 veces). El README informa una mejora de 231 a 185 segundos con otro dataset sin semilla; no la pudimos reproducir, y con ruido de hasta 1,7 veces entre corridas esa diferencia de 20 % no es concluyente. Los tiempos son de una sola máquina: sirven para comparar versiones entre sí.");
  s.addImage({ path: path.join(IMG, "evolucion-tiempo.png"), x: 0.5, y: 1.15, w: 4.4, h: 2.64, altText: "Tiempo total según la cantidad de usuarios: Base 33 s, Eficiente 44 s y Optimizada 94 ms con 2.000 usuarios" });
  s.addImage({ path: path.join(IMG, "evolucion-aceleracion.png"), x: 5.1, y: 1.15, w: 4.4, h: 2.64, altText: "Aceleración respecto de Base por etapa: la similitud es 818 veces más rápida en Optimizada" });
  cifra(s, 0.5, 3.95, 2.0, "350×", "Optimizada vs Base", GREEN);
  cifra(s, 2.65, 3.95, 2.0, "818×", "solo la similitud", GREEN);
  tarjeta(s, 4.8, 3.95, 4.7, 1.05, "FFF4E5");
  s.addText([{ text: "Salvedad: ", options: { bold: true, color: ORANGE } }, { text: "en este banco la Eficiente no supera a la Base en la similitud (0,75×); el costo de armar sets por cada par pesa más que la búsqueda ingenua.", options: { color: INK } }],
    { x: 4.95, y: 4.0, w: 4.4, h: 0.95, fontFace: BODY, fontSize: 12, margin: 0, valign: "middle", isTextBox: true });
}

// ---------------------------------------------------------------- 8 historial
{
  const s = contenido("Sin regresiones en el Parcial 3",
    "[Ricardo, 1 min] Medimos Optimizada en el código de cada tag, de parcial3-fase0 a fase5, con 1.000 usuarios. El tiempo bajó de 68 a unos 31 milisegundos en la Fase 1, gracias al refactor que pedían las reglas de complejidad, y se mantuvo plano: las Fases 2 a 5 sumaron CI, seguridad, documentación y tests sin ningún costo de rendimiento, que es lo que el control de benchmarks del CI debe garantizar.\n\nUna curiosidad honesta: una primera pasada simple mostró las fases 4 y 5 un 50 % más lentas. Era ruido de la máquina: el código del núcleo es idéntico al de la fase 3, y alternando las corridas dieron lo mismo. Por eso el historial intercala cuatro rondas y se queda con la mejor de cada fase. La cobertura es 100 % desde la Fase 1.");
  s.addImage({ path: path.join(IMG, "evolucion-historial.png"), x: 0.5, y: 1.2, w: 5.6, h: 3.36, altText: "Tiempo total de Optimizada en cada fase del Parcial 3: 68 ms en la fase 0 y alrededor de 31 ms desde la fase 1" });
  cifra(s, 6.4, 1.2, 3.1, "68 → 31 ms", "Fase 0 → Fase 1", GREEN);
  lista(s, ["Fases 2 a 5: CI, seguridad, documentación y tests sin costo de rendimiento", "Una pasada simple mostró +50 % en las fases 4 y 5: era ruido de hasta 1,7×"], 6.4, 2.5, 3.1, 2.4, 14);
}

// ---------------------------------------------------------------- 9 resultado
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addText("Resultado final", { x: 0.5, y: 0.3, w: 9, h: 0.7, fontFace: HEAD, fontSize: 30, bold: true, color: "FFFFFF", margin: 0, isTextBox: true, valign: "middle" });
  s.addNotes("[Octavio, 1 min] Para cerrar: la tabla completa. Los tests pasaron de 11 a 88, la cobertura de 70,7 a 100 %, todas las funciones están en rango A, mypy y Ruff en cero, recommend_movies es 2,2 veces más rápido y la memoria del paralelo, plana.\n\nLímites que conocemos y dejamos documentados: las mediciones son de una sola máquina; los diagramas Mermaid se cargan desde unpkg en el navegador; Material for MkDocs llega a fin de vida en mayo de 2027, con Zensical como sucesor; y Windows y macOS no están cubiertos por el CI. Para la demo vamos a mostrar el CI en acción: correr los controles en local, ver cómo se rechaza un cambio que rompe uno y recorrer los gráficos de evolución.");
  const f = (t, b) => ({ text: t, options: { bold: !!b, color: b ? "FFFFFF" : "E4E7EB", fontFace: BODY, fontSize: 14, valign: "middle" } });
  const filas = [["Control", "Parcial 2", "Parcial 3"], ["Tests", "11", "88"], ["Cobertura", "70,7 %", "100 %"], ["Complejidad (Xenon)", "4 funciones en B", "todas en A"],
    ["Errores de mypy", "6", "0"], ["Hallazgos de Ruff", "33", "0"], ["recommend_movies", "447 ms", "198 ms"], ["Memoria del paralelo", "67 MB", "9,3 MB"]];
  s.addTable(filas.map((r, i) => r.map((c, j) => ({ text: c, options: { bold: i === 0 || j === 2, color: i === 0 ? "FFFFFF" : j === 2 ? "7BDFBF" : "E4E7EB", fill: { color: i === 0 ? "3E4C59" : i % 2 ? "27323D" : NAVY }, fontFace: BODY, fontSize: 14, valign: "middle", align: j === 0 ? "left" : "center" } }))),
    { x: 0.5, y: 1.2, w: 5.6, colW: [2.2, 1.7, 1.7], rowH: 0.42, border: { type: "none" } });
  s.addText("Límites conocidos", { x: 6.5, y: 1.2, w: 3, h: 0.4, fontFace: HEAD, fontSize: 16, bold: true, color: "FFFFFF", margin: 0, isTextBox: true });
  s.addText(["Mediciones de una sola máquina", "Mermaid se carga desde unpkg", "Material for MkDocs: fin de vida en mayo de 2027", "Windows y macOS fuera del CI"].map((t, i, a) => ({ text: t, options: { bullet: true, breakLine: i < a.length - 1, paraSpaceAfter: 6 } })),
    { x: 6.5, y: 1.7, w: 3, h: 2.2, fontFace: BODY, fontSize: 14, color: "E4E7EB", margin: 0, valign: "top", isTextBox: true });
  s.addText("Sigue: la demo", { x: 6.5, y: 4.2, w: 3, h: 0.5, fontFace: HEAD, fontSize: 20, bold: true, color: "7BDFBF", margin: 0, isTextBox: true });
}

pres.writeFile({ fileName: path.join(__dirname, "parcial3.pptx") }).then((f) => console.log("escrito", f));
