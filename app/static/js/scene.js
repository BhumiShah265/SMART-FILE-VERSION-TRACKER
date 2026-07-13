/*
 * Smart File — shared WebGL "Version Stack" scene (pastel light theme).
 * Renders soft translucent version cards cascading into depth,
 * linked by a glowing commit spine, with drifting data particles.
 * Camera responds to mouse parallax + page scroll.
 *
 * Requires THREE (global build) to be loaded before this file.
 * Usage: SmartFileScene.mount('#bg-canvas', { density: 12 })
 */
(function () {
  "use strict";

  var PERIWINKLE = 0x8fa7f3;
  var MINT = 0x7fd6bd;
  var PEACH = 0xf6b79e;
  var NODE_COLORS = [PERIWINKLE, MINT, PEACH];

  var prefersReduced =
    typeof window !== "undefined" &&
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- build a "version card" canvas texture (light glass) ---- */
  function makeCardTexture(index) {
    var c = document.createElement("canvas");
    c.width = 512;
    c.height = 340;
    var ctx = c.getContext("2d");

    // soft glass background
    var grad = ctx.createLinearGradient(0, 0, 512, 340);
    grad.addColorStop(0, "rgba(255,255,255,0.97)");
    grad.addColorStop(1, "rgba(238,240,250,0.97)");
    roundRect(ctx, 0, 0, 512, 340, 30);
    ctx.fillStyle = grad;
    ctx.fill();

    // border
    ctx.lineWidth = 3;
    ctx.strokeStyle = "rgba(143,167,243,0.5)";
    ctx.stroke();

    // top accent bar
    roundRect(ctx, 0, 0, 512, 8, 4);
    ctx.fillStyle = "rgba(143,167,243,0.95)";
    ctx.fill();

    // header dot + hash
    ctx.beginPath();
    ctx.arc(48, 60, 10, 0, Math.PI * 2);
    ctx.fillStyle = "#8FA7F3";
    ctx.fill();

    ctx.font = "22px monospace";
    ctx.fillStyle = "#E39A6E";
    var hashes = ["#a3f9e21", "#c771b04", "#f02de88", "#4b1c9aa", "#9de00c3", "#12ab77f"];
    ctx.fillText(hashes[index % hashes.length], 72, 68);

    // faux diff lines
    var lineDefs = [
      ["#A9AEC9", 0.62],
      ["#7FD6BD", 0.44],
      ["#A9AEC9", 0.72],
      ["#F1A0A0", 0.38],
      ["#A9AEC9", 0.55],
      ["#7FD6BD", 0.5],
      ["#A9AEC9", 0.66],
    ];
    var y = 110;
    for (var i = 0; i < lineDefs.length; i++) {
      var seed = (index + 1) * (i + 3);
      var w = (0.3 + ((seed * 37) % 60) / 100) * lineDefs[i][1] * 512;
      roundRect(ctx, 42, y, w, 15, 7);
      ctx.fillStyle = lineDefs[i][0];
      ctx.globalAlpha = 0.7;
      ctx.fill();
      ctx.globalAlpha = 1;
      y += 27;
    }

    // big version label
    ctx.font = "700 42px sans-serif";
    ctx.fillStyle = "#4A4E6D";
    ctx.fillText("v" + (index + 1), 42, 318);

    var tex = new THREE.CanvasTexture(c);
    tex.anisotropy = 4;
    return tex;
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  /* ---- radial glow sprite for spine nodes ---- */
  function makeGlowTexture() {
    var c = document.createElement("canvas");
    c.width = 128;
    c.height = 128;
    var ctx = c.getContext("2d");
    var g = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
    g.addColorStop(0, "rgba(255,255,255,1)");
    g.addColorStop(0.25, "rgba(255,255,255,0.7)");
    g.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, 128, 128);
    return new THREE.CanvasTexture(c);
  }

  function mount(selector, opts) {
    if (typeof THREE === "undefined") return null;
    var canvas =
      typeof selector === "string" ? document.querySelector(selector) : selector;
    if (!canvas) return null;

    opts = opts || {};
    var density = opts.density || 12;
    var scrollDriven = opts.scrollDriven !== false;

    var scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0xeef0fa, 0.05);

    var camera = new THREE.PerspectiveCamera(
      55,
      window.innerWidth / window.innerHeight,
      0.1,
      100
    );
    camera.position.set(0, 0, 7);

    var renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      alpha: true,
      antialias: true,
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    var isMobile = window.innerWidth < 768;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, isMobile ? 1.5 : 2));

    // lights (for the card sheen)
    scene.add(new THREE.AmbientLight(0xffffff, 0.85));
    var key = new THREE.PointLight(PERIWINKLE, 1.0, 50);
    key.position.set(6, 6, 8);
    scene.add(key);
    var fill = new THREE.PointLight(PEACH, 0.5, 50);
    fill.position.set(-7, -4, 6);
    scene.add(fill);

    var group = new THREE.Group();
    scene.add(group);

    var glowTex = makeGlowTexture();
    var cardGeo = new THREE.PlaneGeometry(2.7, 1.8);
    var cards = [];
    var nodePoints = [];

    for (var i = 0; i < density; i++) {
      var tex = makeCardTexture(i);
      var mat = new THREE.MeshBasicMaterial({
        map: tex,
        transparent: true,
        opacity: 0.96,
        side: THREE.DoubleSide,
        depthWrite: false,
      });
      var mesh = new THREE.Mesh(cardGeo, mat);

      var bx = Math.sin(i * 0.7) * 2.1;
      var by = Math.cos(i * 0.55) * 1.1;
      var bz = -i * 2.35;
      mesh.position.set(bx, by, bz);
      mesh.rotation.set(
        Math.sin(i * 0.4) * 0.12,
        Math.sin(i * 0.6) * 0.35,
        Math.cos(i * 0.5) * 0.05
      );
      mesh.userData = { bx: bx, by: by, bz: bz, phase: i * 0.6 };
      group.add(mesh);
      cards.push(mesh);

      // spine node glow
      var spriteMat = new THREE.SpriteMaterial({
        map: glowTex,
        color: NODE_COLORS[i % NODE_COLORS.length],
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      var sprite = new THREE.Sprite(spriteMat);
      sprite.scale.set(1.3, 1.3, 1);
      sprite.position.set(bx, by, bz + 0.05);
      group.add(sprite);

      nodePoints.push(new THREE.Vector3(bx, by, bz));
    }

    // glowing commit spine through the nodes
    if (nodePoints.length > 1) {
      var curve = new THREE.CatmullRomCurve3(nodePoints);
      var pts = curve.getPoints(density * 12);
      var spineGeo = new THREE.BufferGeometry().setFromPoints(pts);
      var spineMat = new THREE.LineBasicMaterial({
        color: PERIWINKLE,
        transparent: true,
        opacity: 0.6,
        blending: THREE.AdditiveBlending,
      });
      group.add(new THREE.Line(spineGeo, spineMat));
    }

    // drifting data particles
    var pCount = isMobile ? 260 : 520;
    var pGeo = new THREE.BufferGeometry();
    var pPos = new Float32Array(pCount * 3);
    for (var p = 0; p < pCount; p++) {
      pPos[p * 3] = (Math.random() - 0.5) * 22;
      pPos[p * 3 + 1] = (Math.random() - 0.5) * 16;
      pPos[p * 3 + 2] = -Math.random() * (density * 2.4);
    }
    pGeo.setAttribute("position", new THREE.BufferAttribute(pPos, 3));
    var pMat = new THREE.PointsMaterial({
      color: 0xb9c4ff,
      size: 0.04,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    var particles = new THREE.Points(pGeo, pMat);
    scene.add(particles);

    /* ---- interaction state ---- */
    var mouseX = 0,
      mouseY = 0,
      targetX = 0,
      targetY = 0,
      scrollProg = 0;

    window.addEventListener("mousemove", function (e) {
      targetX = (e.clientX / window.innerWidth - 0.5) * 2;
      targetY = (e.clientY / window.innerHeight - 0.5) * 2;
    });

    function updateScroll() {
      var max = document.body.scrollHeight - window.innerHeight;
      scrollProg = max > 0 ? window.scrollY / max : 0;
    }
    if (scrollDriven) {
      window.addEventListener("scroll", updateScroll, { passive: true });
      updateScroll();
    }

    function onResize() {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }
    window.addEventListener("resize", onResize);

    var clock = new THREE.Clock();
    var running = true;

    function animate() {
      if (!running) return;
      requestAnimationFrame(animate);
      var t = clock.getElapsedTime();

      // parallax
      mouseX += (targetX - mouseX) * 0.05;
      mouseY += (targetY - mouseY) * 0.05;

      // fly through the stack on scroll
      var flyZ = 7 - scrollProg * density * 2.05;
      camera.position.x += (mouseX * 1.4 - camera.position.x) * 0.06;
      camera.position.y += (-mouseY * 0.9 - camera.position.y) * 0.06;
      camera.position.z += (flyZ - camera.position.z) * 0.06;
      camera.lookAt(mouseX * 0.6, -mouseY * 0.4, camera.position.z - 6);

      if (!prefersReduced) {
        for (var i = 0; i < cards.length; i++) {
          var m = cards[i];
          var d = m.userData;
          m.position.y = d.by + Math.sin(t * 0.6 + d.phase) * 0.18;
          m.position.x = d.bx + Math.cos(t * 0.4 + d.phase) * 0.12;
          m.rotation.y = Math.sin(t * 0.3 + d.phase) * 0.35;
        }
        group.rotation.z = Math.sin(t * 0.1) * 0.02;
        particles.rotation.y = t * 0.02;
        var pa = particles.geometry.attributes.position.array;
        for (var q = 0; q < pCount; q++) {
          pa[q * 3 + 1] += 0.004;
          if (pa[q * 3 + 1] > 8) pa[q * 3 + 1] = -8;
        }
        particles.geometry.attributes.position.needsUpdate = true;
      }

      renderer.render(scene, camera);
    }
    animate();

    document.addEventListener("visibilitychange", function () {
      running = !document.hidden;
      if (running) {
        clock.getDelta();
        animate();
      }
    });

    return { scene: scene, camera: camera, renderer: renderer };
  }

  window.SmartFileScene = { mount: mount };
})();
