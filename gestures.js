function apply(tr, xys) {
	const [axx, axy, ayx, ayy, atx, aty] = tr;
	return xys.map(([x, y]) => [axx * x + ayx * y + atx, axy * x + ayy * y + aty]);
}

function _petoinit(x) {
	const glyphs = [];
	const {baseglyphs} = x;
	const r = 4;
	for (const {glyph, gestures, symmetries} of baseglyphs) {
		// if (gestures.length === 2) continue;
		for (const symm of symmetries) {
			const [axx, axy, ayx, ayy, atx, aty] = symm;
			for (let dx = 0; dx < r * 64; dx += 64) {
				for (let dy = 0; dy < r * 64; dy += 64) {
					const s = [axx, axy, ayx, ayy, atx + dx, aty + dy];
					glyphs.push({
						gesture: apply(s, gestures),
						glyph: {
							d: glyph,
							matrix: s,
						},
					});
					glyphs.push({
						gesture: apply(s, gestures).reverse(),
						glyph: {
							d: glyph,
							matrix: s,
						},
					});
				}
			}
			// writeText(JSON.stringify(gestures.map(([x, y]) => [axx * x + ayx * y + atx, axy * x + ayy * y + aty])));
			// writeTag("br");
			// const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
			// svg.setAttribute("width", "64");
			// svg.setAttribute("height", "64");
			// const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
			// path.setAttribute("style", "fill:black;stroke:none");
			// path.setAttribute("d", glyph);
			// path.setAttribute("transform", `matrix(${symm})`);
			// svg.appendChild(path);
			// document.body.appendChild(svg);
			// writeTag("hr");
		}
	}
	const idle = {};
	for (let i = 0; i < glyphs.length; ++i) {
		const [x, y] = glyphs[i].gesture[0];
		idle[[x, y]] = i;
		for (let dx = -1; dx <= 1; ++dx) {
			for (let dy = -1; dy <= 1; ++dy) {
				if (idle[[x + dx, y + dy]] == null) idle[[x + dx, y + dy]] = i;
			}
		}
	}
	const canvas = document.getElementById("canvas");
	const indicator = document.getElementById("indicator");
	const placement = document.getElementById("placement");
	const path = placement.querySelector("path");
	const debug = document.getElementById("debug");
	const width = 64 * r;
	const height = 64 * r;
	let cliXpx = canvas.clientLeft;
	let cliYpx = canvas.clientTop;
	let offXpx = cliXpx + canvas.offsetLeft;
	let offYpx = cliYpx + canvas.offsetTop;
	let widthpx = ((canvas.clientWidth / width)|0)*width;
	let heightpx = ((canvas.clientHeight / height)|0)*height;
	window.addEventListener("resize", () => {
		cliXpx = canvas.clientLeft;
		cliYpx = canvas.clientTop;
		offXpx = cliXpx + canvas.offsetLeft;
		offYpx = cliYpx + canvas.offsetTop;
		widthpx = ((canvas.clientWidth / width)|0)*width;
		heightpx = ((canvas.clientHeight / height)|0)*height;
	}, false);
	const eventToVirtual = (clientX, clientY) =>
		[0|((clientX - offXpx) / widthpx * width), 0|((clientY - offYpx) / heightpx * height)];
	const virtualToRelative = (xy) => {
		const [x, y] = xy;
		return [widthpx * x / width, heightpx * y / height];
	};
	let currentGesturePosition;
	const maxDd = 4*4;
	function startGestures(vxy) {
		const [x, y] = vxy;
		currentGesturePosition = [];
		for (let i = 0; i < glyphs.length; ++i) {
			const glyph = glyphs[i];
			const [tx, ty] = glyph.gesture[0];
			const dd = (tx - x) * (tx - x) + (ty - y) * (ty - y);
			if (dd >= maxDd) continue;
			currentGesturePosition.push({i, c: [[tx, ty]], glyph});
		}
		debug.textContent = JSON.stringify(currentGesturePosition);
	}
	function updateGestures(vxy) {
		const [x, y] = vxy;
		if (currentGesturePosition == null) {
			if (idle[[x, y]] != null) return [idle[[x, y]], false];
			return [-1, false];
		}
		if (currentGesturePosition.length === 0) return [-1, false];
		let maxDd = 4*4;
		let bestDd = maxDd;
		let bestIndex = currentGesturePosition[0].i;
		let ac = false;
		for (const {i, c, glyph} of currentGesturePosition) {
			if (c.length < glyph.gesture.length) {
				const [tx, ty] = glyph.gesture[c.length];
				const dd = (tx - x) * (tx - x) + (ty - y) * (ty - y);
				if (dd < maxDd) {
					c.push([x, y]);
				}
			}
			const [tx, ty] = glyph.gesture[c.length - 1];
			const dd = (tx - x) * (tx - x) + (ty - y) * (ty - y);
			const [cx, cy] = c[c.length - 1];
			let cdd = (tx - cx) * (tx - cx) + (ty - cy) * (ty - cy);
			if (dd < cdd) {
				c[c.length - 1] = [x, y];
				cdd = dd;
			}
			if (dd < bestDd) {
				bestDd = dd;
				bestIndex = i;
				ac = c.length === glyph.gesture.length;
			}
		}
		debug.textContent = `${bestDd} ${bestIndex} ${ac} ${bestIndex >= 0 && JSON.stringify(currentGesturePosition[bestIndex])}`;
		return [bestIndex, ac];
	}
	function showPlacement(i) {
		if (i === -1) {
			path.style.display = "none";
			return;
		}
		path.style.display = "";
		path.setAttribute("d", glyphs[i].glyph.d);
		let [axx, axy, ayx, ayy, atx, aty] = glyphs[i].glyph.matrix;
		const sx = widthpx / width;
		const sy = heightpx / height;
		const mat = `matrix(${axx * sx}, ${axy * sy}, ${ayx * sx}, ${ayy * sy}, ${atx * sx}, ${aty * sy})`;
		path.setAttribute("transform", mat);
	}
	let placed = [];
	function addGesture(i) {
		const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
		path.setAttribute("style", "fill:black;stroke:none");
		path.setAttribute("d", glyphs[i].glyph.d);
		let [axx, axy, ayx, ayy, atx, aty] = glyphs[i].glyph.matrix;
		const sx = widthpx / width;
		const sy = heightpx / height;
		const mat = `matrix(${axx * sx}, ${axy * sy}, ${ayx * sx}, ${ayy * sy}, ${atx * sx}, ${aty * sy})`;
		path.setAttribute("transform", mat);
		placement.appendChild(path);
		placed.push(path);
	}
	console.log(glyphs.length);
	canvas.addEventListener("mousedown", (e) => {
		const vxy = eventToVirtual(e.clientX, e.clientY);
		startGestures(vxy);
		const [bestIndex] = updateGestures(vxy);
		showPlacement(bestIndex);
		const [x, y] = virtualToRelative(vxy);
		indicator.style.display = "";
		indicator.style.left = x + "px";
		indicator.style.top = y + "px";
		indicator.style.width = (widthpx / width) + "px";
		indicator.style.height = (heightpx / height) + "px";
	}, false);
	canvas.addEventListener("mousemove", (e) => {
		const vxy = eventToVirtual(e.clientX, e.clientY);
		const [x, y] = virtualToRelative(vxy);
		indicator.style.left = x + "px";
		indicator.style.top = y + "px";
		const [bestIndex] = updateGestures(vxy);
		showPlacement(bestIndex);
	}, false);
	window.addEventListener("mouseup", (e) => {
		const [bestIndex, ac] = updateGestures(eventToVirtual(e.clientX, e.clientY));
		if (ac) addGesture(bestIndex);
		currentGesturePosition = null;
		showPlacement(-1);
		indicator.style.display = "none";
	}, false);
	window.addEventListener("keypress", (e) => {
		if (e.ctrlKey || e.altKey || e.metaKey || e.shiftKey) return;
		if (e.key === "z" && placed.length > 0) {
			const p = placed[placed.length - 1];
			placed.splice(placed.length - 1, 1);
			p.parentNode.removeChild(p);
		}
	}, false);
}
window.addEventListener("load", () => {
	window.petoinit = _petoinit;
	if (window.petodata) _petoinit(window.petodata);
}, false);
