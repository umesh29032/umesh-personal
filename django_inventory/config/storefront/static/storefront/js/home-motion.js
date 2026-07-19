/* Kapil Enterprises — public homepage motion system.
   Stack: GSAP 3.13 (ScrollTrigger + SplitText, free since Webflow acquisition) + Lenis smooth scroll — all vendored, no CDN.
   Fallback chain: prefers-reduced-motion OR libs missing → lightweight IntersectionObserver reveals only.
   Touch devices keep native scrolling; magnetic/tilt/cursor run on fine pointers only. */
(function () {
    'use strict';
    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var finePointer = window.matchMedia('(pointer: fine)').matches;

    /* ── Fallback: plain IO reveals (same behavior the page had pre-GSAP) ── */
    function basicReveals() {
        if (reduceMotion || !('IntersectionObserver' in window)) return;
        var targets = [];
        document.querySelectorAll('.section-header, .about-copy, .about-panel, .cta-inner').forEach(function (el) { targets.push(el); });
        document.querySelectorAll('.cat-grid, .product-grid, .why-grid, .reveal-stagger').forEach(function (group) {
            Array.prototype.forEach.call(group.children, function (child, i) {
                child.style.setProperty('--rd', Math.min(i * 0.07, 0.35) + 's');
                targets.push(child);
            });
        });
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) { entry.target.classList.add('in-view'); io.unobserve(entry.target); }
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
        targets.forEach(function (el) { el.classList.add('reveal'); io.observe(el); });
    }

    if (reduceMotion || !window.gsap || !window.ScrollTrigger || !window.SplitText || !window.Lenis) {
        basicReveals();
        return;
    }

    /* SplitText measures line boxes — must wait for webfonts or masks split on fallback metrics */
    document.fonts.ready.then(initMotion);

    function initMotion() {
    gsap.registerPlugin(ScrollTrigger, SplitText);

    /* ── Lenis smooth scroll driven by the GSAP ticker (keeps ScrollTrigger frame-synced) ── */
    var lenis = new Lenis({ lerp: 0.11, autoRaf: false });
    lenis.on('scroll', ScrollTrigger.update);
    gsap.ticker.add(function (t) { lenis.raf(t * 1000); });
    gsap.ticker.lagSmoothing(0);

    /* anchor links glide via lenis (84px fixed-navbar offset) */
    document.querySelectorAll('a[href^="#"]').forEach(function (a) {
        a.addEventListener('click', function (e) {
            var target = document.querySelector(a.getAttribute('href'));
            if (!target) return;
            e.preventDefault();
            lenis.scrollTo(target, { offset: -84, duration: 1.2 });
        });
    });

    /* ── Kinetic hero typography: masked lines, chars rise with 3D pitch ── */
    var heroSplit = SplitText.create('.hero-title', { type: 'chars,lines', mask: 'lines' });
    gsap.from(heroSplit.chars, { yPercent: 115, rotateX: -35, stagger: 0.03, duration: 1.15, ease: 'expo.out', delay: 0.25 });

    /* ── Section headers: tag → masked word rise → supporting copy ── */
    document.querySelectorAll('.section-header, .about-copy').forEach(function (header) {
        var tl = gsap.timeline({ scrollTrigger: { trigger: header, start: 'top 85%', once: true } });
        var tag = header.querySelector('.section-tag');
        var title = header.querySelector('.section-title, .about-title');
        if (tag) tl.from(tag, { y: 16, autoAlpha: 0, duration: 0.5, ease: 'power2.out', clearProps: 'all' });
        if (title) {
            var split = SplitText.create(title, { type: 'words,lines', mask: 'lines' });
            tl.from(split.words, { yPercent: 120, stagger: 0.05, duration: 0.85, ease: 'expo.out' }, '-=0.25');
        }
        var rest = header.querySelectorAll('.section-desc, .about-lede, p, .about-values, .about-quote');
        if (rest.length) tl.from(rest, { y: 24, autoAlpha: 0, stagger: 0.08, duration: 0.6, ease: 'power2.out', clearProps: 'all' }, '-=0.4');
    });

    /* CTA banner heading */
    var cta = document.querySelector('.cta-inner');
    if (cta) {
        var ctaTl = gsap.timeline({ scrollTrigger: { trigger: cta, start: 'top 85%', once: true } });
        var ctaH = cta.querySelector('h2');
        if (ctaH) {
            var ctaSplit = SplitText.create(ctaH, { type: 'words,lines', mask: 'lines' });
            ctaTl.from(ctaSplit.words, { yPercent: 120, stagger: 0.06, duration: 0.9, ease: 'expo.out' });
        }
        ctaTl.from(cta.querySelectorAll('p, .cta-buttons'), { y: 24, autoAlpha: 0, stagger: 0.1, duration: 0.6, clearProps: 'all' }, '-=0.4');
    }

    /* ── Card grids: batched rise-in (clearProps restores CSS hover transforms after) ── */
    gsap.utils.toArray('.cat-grid, .product-grid, .why-grid, .showcase-grid').forEach(function (grid) {
        gsap.from(grid.children, {
            y: 40, autoAlpha: 0, stagger: 0.08, duration: 0.7, ease: 'power3.out',
            clearProps: 'transform,opacity,visibility',
            scrollTrigger: { trigger: grid, start: 'top 85%', once: true }
        });
    });

    /* ── Parallax: hero deco letter + showcase drift + about panel float (guard: sections are data-dependent) ── */
    gsap.to('.hero-deco', { yPercent: -22, ease: 'none', scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true } });
    if (document.querySelector('.showcase-grid')) {
        gsap.to('.showcase-grid', { y: -40, ease: 'none', scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true } });
    }
    if (document.querySelector('.hero-atelier')) {
        gsap.to('.hero-atelier', { y: -50, ease: 'none', scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true } });
        /* mouse-depth: chips drift opposite the pointer (fine pointers). CSS float animation
           owns transform and would override GSAP's inline x/y — so here GSAP takes the
           transform over entirely: animation off, float re-created as a yPercent yoyo
           (yPercent + x/y are separate GSAP channels, they compose). Touch keeps CSS float. */
        if (finePointer) {
            var chips = gsap.utils.toArray('.atelier-chip');
            var hero = document.querySelector('.hero');
            var chipTos = chips.map(function (chip, i) {
                chip.style.animation = 'none';
                gsap.to(chip, { yPercent: -9, yoyo: true, repeat: -1, duration: 2.8, ease: 'sine.inOut', delay: i * 0.9 });
                return {
                    x: gsap.quickTo(chip, 'x', { duration: 0.8, ease: 'power2.out' }),
                    y: gsap.quickTo(chip, 'y', { duration: 0.8, ease: 'power2.out' }),
                    depth: (i + 1) * 8
                };
            });
            hero.addEventListener('mousemove', function (e) {
                var nx = (e.clientX / window.innerWidth) - 0.5;
                var ny = (e.clientY / window.innerHeight) - 0.5;
                chipTos.forEach(function (c) { c.x(-nx * c.depth * 2); c.y(-ny * c.depth); });
            }, { passive: true });
        }
    }
    if (document.querySelector('.about-panel')) {
        gsap.to('.about-panel', { y: -30, ease: 'none', scrollTrigger: { trigger: '.about', start: 'top bottom', end: 'bottom top', scrub: true } });
    }

    /* ── Process timeline: steps rise, connecting thread draws with scroll ── */
    if (document.querySelector('.process-list')) {
        gsap.from('.process-step', {
            y: 30, autoAlpha: 0, stagger: 0.12, duration: 0.6, ease: 'power2.out',
            clearProps: 'transform,opacity,visibility',
            scrollTrigger: { trigger: '.process-list', start: 'top 80%', once: true }
        });
        gsap.utils.toArray('.process-step').forEach(function (step) {
            gsap.fromTo(step, { '--draw': 0 }, {
                '--draw': 1, ease: 'none',
                scrollTrigger: { trigger: step, start: 'top 78%', end: 'bottom 62%', scrub: 0.6 }
            });
        });
        gsap.from('.about-panel-foot', {
            autoAlpha: 0, y: 16, duration: 0.6, clearProps: 'all',
            scrollTrigger: { trigger: '.about-panel-foot', start: 'top 88%', once: true }
        });
    }

    /* ── Marquee: scroll-velocity skew on the WRAPPER (track's transform belongs to the CSS loop) ── */
    var skewSetter = gsap.quickSetter('.marquee', 'skewX', 'deg');
    var clampSkew = gsap.utils.clamp(-5, 5);
    var skewProxy = { skew: 0 };
    ScrollTrigger.create({
        onUpdate: function (self) {
            var skew = clampSkew(self.getVelocity() / -300);
            if (Math.abs(skew) > Math.abs(skewProxy.skew)) {
                skewProxy.skew = skew;
                gsap.to(skewProxy, { skew: 0, duration: 0.8, ease: 'power3.out', overwrite: true, onUpdate: function () { skewSetter(skewProxy.skew); } });
            }
        }
    });

    /* ── Fine-pointer flourishes (desktop only) ── */
    if (finePointer) {
        /* trailing cursor ring — native cursor stays (B2B usability), copper ring follows */
        var ring = document.createElement('div');
        ring.className = 'cursor-ring';
        document.body.appendChild(ring);
        var ringX = gsap.quickTo(ring, 'x', { duration: 0.35, ease: 'power3.out' });
        var ringY = gsap.quickTo(ring, 'y', { duration: 0.35, ease: 'power3.out' });
        window.addEventListener('mousemove', function (e) { ring.classList.add('is-live'); ringX(e.clientX); ringY(e.clientY); }, { passive: true });
        document.querySelectorAll('a, button').forEach(function (el) {
            el.addEventListener('mouseenter', function () { ring.classList.add('is-active'); });
            el.addEventListener('mouseleave', function () { ring.classList.remove('is-active'); });
        });

        /* magnetic CTAs */
        document.querySelectorAll('.btn-hero-primary, .nav-cta').forEach(function (btn) {
            btn.setAttribute('data-magnetic', '');
            var mx = gsap.quickTo(btn, 'x', { duration: 0.4, ease: 'power3.out' });
            var my = gsap.quickTo(btn, 'y', { duration: 0.4, ease: 'power3.out' });
            btn.addEventListener('mousemove', function (e) {
                var r = btn.getBoundingClientRect();
                mx((e.clientX - r.left - r.width / 2) * 0.25);
                my((e.clientY - r.top - r.height / 2) * 0.35);
            });
            btn.addEventListener('mouseleave', function () { mx(0); my(0); });
        });

        /* 3D tilt cards */
        document.querySelectorAll('.showcase-card, .product-card, .cat-card, .why-card').forEach(function (card) {
            card.setAttribute('data-tilt', '');
            gsap.set(card, { transformPerspective: 900 });
            var rx = gsap.quickTo(card, 'rotationX', { duration: 0.5, ease: 'power2.out' });
            var ry = gsap.quickTo(card, 'rotationY', { duration: 0.5, ease: 'power2.out' });
            card.addEventListener('mousemove', function (e) {
                var r = card.getBoundingClientRect();
                rx(gsap.utils.mapRange(0, r.height, 6, -6, e.clientY - r.top));
                ry(gsap.utils.mapRange(0, r.width, -6, 6, e.clientX - r.left));
            });
            card.addEventListener('mouseenter', function () { gsap.to(card, { scale: 1.02, duration: 0.35, ease: 'power2.out' }); });
            card.addEventListener('mouseleave', function () { rx(0); ry(0); gsap.to(card, { scale: 1, duration: 0.35, ease: 'power2.out' }); });
        });
    }
    }  /* end initMotion */
})();
