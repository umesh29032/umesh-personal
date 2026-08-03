/* KEParticles — vanilla canvas "thread-spark" field (no library).
   Copper/cream dust drifting upward + constellation lines between near pairs,
   gentle cursor repulsion on fine pointers. Shared by the public homepage hero
   and the login brand panel.
   Budget-device safe: DPR-capped, count scales with area, pauses when the tab
   is hidden or the host is offscreen, refuses to start under
   prefers-reduced-motion. */
(function () {
    'use strict';

    function attach(host, opts) {
        opts = opts || {};
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return null;
        if (!host || !host.offsetParent && getComputedStyle(host).position !== 'fixed') {
            if (!host || host.offsetWidth === 0) return null;   // host hidden (e.g. auth brand panel on phones)
        }

        var canvas = document.createElement('canvas');
        canvas.className = opts.className || 'ke-particles';
        canvas.setAttribute('aria-hidden', 'true');
        host.appendChild(canvas);
        var ctx = canvas.getContext('2d');

        var dpr = 1;
        var W = 0, H = 0, parts = [], running = true, visible = true, stopped = false, raf = null;
        var mouse = { x: -9999, y: -9999 };
        var fine = window.matchMedia('(pointer: fine)').matches;
        var LINK_DIST = opts.linkDist || 110;

        function size() {
            dpr = Math.min(window.devicePixelRatio || 1, 2);   // re-read: window may move between monitors
            W = host.clientWidth; H = host.clientHeight;
            canvas.width = W * dpr; canvas.height = H * dpr;
            canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            var target = Math.min(opts.max || 70, Math.round(W * H / (opts.density || 16000)));
            while (parts.length < target) parts.push(spawn(true));
            parts.length = target;
        }

        function spawn(anywhere) {
            return {
                x: Math.random() * W,
                y: anywhere ? Math.random() * H : H + 6,
                r: 0.6 + Math.random() * 1.6,
                vx: (Math.random() - 0.5) * 0.12,
                vy: -(0.1 + Math.random() * 0.3),
                tw: Math.random() * Math.PI * 2,           // twinkle phase
                cream: Math.random() < 0.25                 // 1-in-4 sparks are cream, rest copper
            };
        }

        function step() {
            if (!running || !visible) return;
            ctx.clearRect(0, 0, W, H);
            var i, j, p, q;
            for (i = 0; i < parts.length; i++) {
                p = parts[i];
                p.x += p.vx; p.y += p.vy; p.tw += 0.02;
                if (fine) {
                    var dx = p.x - mouse.x, dy = p.y - mouse.y;
                    var d2 = dx * dx + dy * dy;
                    if (d2 < 10000 && d2 > 1) {             // 100px repulsion radius
                        var f = 60 / d2;
                        p.x += dx * f; p.y += dy * f;
                    }
                }
                if (p.y < -8 || p.x < -8 || p.x > W + 8) { parts[i] = spawn(false); continue; }
                var a = (0.35 + 0.3 * Math.sin(p.tw));
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fillStyle = p.cream ? 'rgba(245,237,224,' + a * 0.7 + ')' : 'rgba(212,146,74,' + a + ')';
                ctx.fill();
            }
            /* constellation threads — counts stay small (≤70) so O(n²) is fine */
            ctx.lineWidth = 0.5;
            for (i = 0; i < parts.length; i++) {
                for (j = i + 1; j < parts.length; j++) {
                    p = parts[i]; q = parts[j];
                    var ddx = p.x - q.x, ddy = p.y - q.y;
                    var dist = Math.sqrt(ddx * ddx + ddy * ddy);
                    if (dist < LINK_DIST) {
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y);
                        ctx.strokeStyle = 'rgba(184,115,51,' + (0.09 * (1 - dist / LINK_DIST)) + ')';
                        ctx.stroke();
                    }
                }
            }
            raf = requestAnimationFrame(step);
        }

        function play() { if (running && visible && !raf) raf = requestAnimationFrame(step); }
        function halt() { if (raf) { cancelAnimationFrame(raf); raf = null; } }

        size();
        window.addEventListener('resize', size);
        if (fine) {
            host.addEventListener('mousemove', function (e) {
                var r = canvas.getBoundingClientRect();
                mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top;
            }, { passive: true });
            host.addEventListener('mouseleave', function () {
                mouse.x = -9999; mouse.y = -9999;   // stop repelling from a stale point
            });
        }
        document.addEventListener('visibilitychange', function () {
            if (stopped) return;                     // a stop()ped instance must stay stopped
            running = !document.hidden;
            running ? play() : halt();
        });
        if ('IntersectionObserver' in window) {
            new IntersectionObserver(function (entries) {
                visible = entries[0].isIntersecting;
                visible ? play() : halt();
            }).observe(host);
        }
        play();
        return { canvas: canvas, stop: function () { stopped = true; running = false; halt(); } };
    }

    window.KEParticles = { attach: attach };
})();
