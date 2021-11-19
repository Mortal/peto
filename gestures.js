function writeTag(tag, text, attrib, owner) {
	const o = document.createElement(tag);
	(owner || document.body).appendChild(o);
	o.textContent = text;
	for (const [k, v] of Object.entries(attrib || {})) {
		o.setAttribute(k, v);
	}
	return o;
}
function writeText(text) {
	document.body.appendChild(document.createTextNode(text));
}
function _petoinit(x) {
	const {baseglyphs} = x;
	for (const {glyph, gestures, symmetries} of baseglyphs) {
		writeTag("h1", "Some glyph");
		for (const symm of symmetries) {
			const [axx, axy, ayx, ayy, atx, aty] = symm;
			writeText(JSON.stringify(gestures.map(([x, y]) => [axx * x + ayx * y + atx, axy * x + ayy * y + aty])));
			writeTag("br");
			const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
			svg.setAttribute("width", "64");
			svg.setAttribute("height", "64");
			const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
			path.setAttribute("style", "fill:black;stroke:none");
			path.setAttribute("d", glyph);
			path.setAttribute("transform", `matrix(${symm})`);
			svg.appendChild(path);
			document.body.appendChild(svg);
			writeTag("hr");
		}
	}
}
window.addEventListener("load", () => {
	window.petoinit = _petoinit;
	if (window.petodata) _petoinit(window.petodata);
}, false);
