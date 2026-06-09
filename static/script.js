// Utility functions
// Force logout when browser is closed and reopened
(function() {
    const sessionToken = sessionStorage.getItem('session_init');
    if (!sessionToken) {
        // This is a fresh browser session (or first visit)
        sessionStorage.setItem('session_init', Date.now().toString());
        // Check if user is logged in via cookie and force logout
        fetch('/api/auth/user', { credentials: 'include' })
            .then(res => res.json())
            .then(data => {
                if (data.isLoggedIn) {
                    fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
                        .then(() => {
                            // Clear any leftover data
                            sessionStorage.clear();
                            localStorage.clear();
                            // Reload to trigger redirect to login
                            window.location.reload();
                        });
                }
            })
            .catch(err => console.warn('Session check failed', err));
    }
})();
document.addEventListener('DOMContentLoaded', () => {
    // === 3D PARTICLES SYSTEM (All Pages) ===
    (function init3DParticles() {
        // Check if canvas already exists
        if (document.getElementById('particles-canvas')) return;
        
        const canvas = document.createElement('canvas');
        canvas.id = 'particles-canvas';
        document.body.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        let particles = [];
        let animationId;
        
        function resize() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        resize();
        window.addEventListener('resize', resize);
        
        // Create 3D particles
        class Particle3D {
            constructor() {
                this.reset();
            }
            
            reset() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.z = Math.random() * 1000; // Depth
                this.size = Math.random() * 3 + 1;
                this.speedX = (Math.random() - 0.5) * 0.5;
                this.speedY = (Math.random() - 0.5) * 0.5;
                this.speedZ = Math.random() * 2 + 1;
                this.color = `hsla(${Math.random() * 60 + 180}, 100%, 70%, ${Math.random() * 0.5 + 0.3})`;
            }
            
            update() {
                this.z -= this.speedZ;
                if (this.z <= 0) {
                    this.z = 1000;
                    this.reset();
                    this.z = 1000;
                }
                
                // 3D projection
                const scale = 500 / (500 + this.z);
                this.screenX = canvas.width / 2 + (this.x - canvas.width / 2) * scale;
                this.screenY = canvas.height / 2 + (this.y - canvas.height / 2) * scale;
                this.screenSize = this.size * scale;
            }
            
            draw() {
                if (this.screenSize < 0.5) return;
                ctx.beginPath();
                ctx.arc(this.screenX, this.screenY, this.screenSize, 0, Math.PI * 2);
                ctx.fillStyle = this.color;
                ctx.fill();
                
                // Glow effect
                ctx.shadowBlur = 10;
                ctx.shadowColor = this.color;
            }
        }
        
        // Initialize particles
        for (let i = 0; i < 150; i++) {
            particles.push(new Particle3D());
        }
        
        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Sort by z for proper depth
            particles.sort((a, b) => b.z - a.z);
            
            particles.forEach(p => {
                p.update();
                p.draw();
            });
            
            ctx.shadowBlur = 0;
            animationId = requestAnimationFrame(animate);
        }
        
        animate();
    })();

    // Ripple effect on buttons
    const buttons = document.querySelectorAll('.btn:not(.no-ripple)');
    buttons.forEach(button => {
        button.addEventListener('click', function (e) {
            let x = e.clientX - e.target.getBoundingClientRect().left;
            let y = e.clientY - e.target.getBoundingClientRect().top;
            let ripples = document.createElement('span');
            ripples.style.left = x + 'px';
            ripples.style.top = y + 'px';
            ripples.classList.add('ripple');
            this.appendChild(ripples);
            setTimeout(() => ripples.remove(), 600);
        });
    });

    // Scroll reveal animation
    const reveals = document.querySelectorAll('.reveal');
    function reveal() {
        for (let i = 0; i < reveals.length; i++) {
            let windowHeight = window.innerHeight;
            let elementTop = reveals[i].getBoundingClientRect().top;
            let elementVisible = 100;
            if (elementTop < windowHeight - elementVisible) {
                reveals[i].classList.add('active');
            }
        }
    }
    window.addEventListener('scroll', reveal);
    reveal();

    // 3D Tilt Effect
    const tiltCards = document.querySelectorAll('.tilt-card');
    tiltCards.forEach(card => {
        card.addEventListener('mousemove', e => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = ((y - centerY) / centerY) * -10;
            const rotateY = ((x - centerX) / centerX) * 10;
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.05, 1.05, 1.05)`;
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
            card.style.transition = 'transform 0.5s ease-out';
            setTimeout(() => {
                card.style.transition = '';
            }, 500);
        });
    });

    // --- Authentication Logic ---
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const loginError = document.getElementById('login-error');
    const regError = document.getElementById('reg-error');
    const regSuccess = document.getElementById('reg-success');
    const logoutBtn = document.getElementById('logout-btn');

    // Tab Switching Logic
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');

    if (tabLogin && tabRegister) {
        tabLogin.addEventListener('click', () => {
            tabLogin.classList.add('active');
            tabRegister.classList.remove('active');
            loginForm.classList.add('active');
            registerForm.classList.remove('active');
        });
        tabRegister.addEventListener('click', () => {
            tabRegister.classList.add('active');
            tabLogin.classList.remove('active');
            registerForm.classList.add('active');
            loginForm.classList.remove('active');
        });
    }

    // Page Protection using backend session
    const isLoginPage = document.body.id === 'login-page';
    const isLandingPage = document.body.id === 'landing-page';

    async function checkAuth() {
        try {
            const res = await fetch('/api/auth/user', { credentials: 'include' });
            const result = await res.json();
            const isLoggedIn = result.isLoggedIn;
            const data = result.user || {};

            if (isLoggedIn) {
                // Update UI with user data
                const userDisplay = document.getElementById('user-name-display');
                if (userDisplay) userDisplay.textContent = data.fullName || data.username;

                // Update Topbar Profile
                const userIcon = document.querySelector('#topbar-profile-btn i.fa-user');
                if (userIcon && data.profileImage) {
                    const img = document.createElement('img');
                    img.src = data.profileImage;
                    img.className = 'profile-pic-small';
                    userIcon.parentNode.replaceChild(img, userIcon);
                }

                // Update Sidebar Profile
                const sideName = document.getElementById('side-username');
                const sideImg = document.getElementById('side-profile-img');
                if (sideName) sideName.textContent = data.fullName || data.username;
                if (sideImg && data.profileImage) sideImg.src = data.profileImage;
            }

            // Redirect if needed
            if (!isLoginPage && !isLandingPage && !isLoggedIn && !window.location.pathname.includes('reset.html') && !window.location.pathname.includes('verify-otp.html')) {
                window.location.replace('login.html');
            }
            if (isLoginPage && isLoggedIn) {
                window.location.href = 'dashboard.html';
            }
        } catch (err) {
            console.error('Auth check error:', err);
            if (!isLoginPage && !isLandingPage) window.location.replace('login.html');
        }
    }

    checkAuth();

    // Profile Image Preview Helper
    const regImageInput = document.getElementById('reg-image');
    if (regImageInput) {
        regImageInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const label = document.querySelector('.file-label');
                    label.textContent = file.name;
                    label.dataset.base64 = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // --- Registration Validation & Submission ---
    if (registerForm) {
        const regInputs = {
            fullname: document.getElementById('reg-fullname'),
            email: document.getElementById('reg-email'),
            phone: document.getElementById('reg-phone'),
            username: document.getElementById('reg-username'),
            password: document.getElementById('reg-password'),
            linkedin: document.getElementById('reg-linkedin'),
            github: document.getElementById('reg-github')
        };

        const validateField = (field, value) => {
            const errEl = document.getElementById(`err-reg-${field}`);
            const groupEl = regInputs[field].closest('.input-group');
            let error = '';

            switch (field) {
                case 'fullname':
                    if (!value) error = 'Full Name is required';
                    else if (value.length < 3) error = 'Full Name must be at least 3 characters';
                    else if (value.length > 25) error = 'Full Name must be maximum 25 characters';
                    else if (!/^[a-zA-Z\s]+$/.test(value)) error = 'Full Name must contain only letters and spaces';
                    break;
                case 'email':
                    if (!value) error = 'Email is required';
                    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) error = 'Invalid email format';
                    break;
                case 'phone':
                    if (!value) error = 'Phone is required';
                    else if (!/^\d+$/.test(value)) error = 'Phone number must contain only numbers';
                    else if (value.length !== 10) error = 'Phone number must be exactly 10 digits';
                    break;
                case 'username':
                    if (!value) error = 'Username is required';
                    else if (!/^[a-zA-Z0-9]{4,}$/.test(value)) error = 'Only letters/numbers, no spaces, min 4 chars';
                    break;
                case 'password':
                    if (!value) error = 'Password is required';
                    else if (value.length < 6) error = 'Minimum 6 characters required';
                    else if (!/(?=.*[A-Za-z])(?=.*\d)/.test(value)) error = 'Must contain at least 1 letter and 1 number';
                    break;
                case 'linkedin':
                    if (value && !/^https?:\/\/(www\.)?linkedin\.com\/in\/[a-zA-Z0-9\-_%]+\/?$/.test(value)) {
                        error = 'Enter a valid LinkedIn profile URL (e.g., https://linkedin.com/in/username)';
                    }
                    break;
                case 'github':
                    if (value && !/^https?:\/\/(www\.)?github\.com\/[a-zA-Z0-9\-_]+\/?$/.test(value)) {
                        error = 'Enter a valid GitHub profile URL (e.g., https://github.com/username)';
                    }
                    break;
            }
            if (error) {
                errEl.textContent = '❌ ' + error;
                groupEl.classList.add('invalid');
                groupEl.classList.remove('valid');
                return false;
            } else {
                errEl.textContent = '';
                groupEl.classList.remove('invalid');
                if (value) groupEl.classList.add('valid');
                return true;
            }
        };

        // Real-time validation: Clear error when user starts typing
        Object.keys(regInputs).forEach(key => {
            regInputs[key].addEventListener('input', (e) => {
                let val = regInputs[key].value;
                if (key === 'phone') {
                    val = val.replace(/\D/g, '');
                    if (val.length > 10) val = val.substring(0, 10);
                    regInputs[key].value = val;
                } else if (key === 'fullname') {
                    val = val.replace(/[^a-zA-Z\s]/g, '');
                    if (val.length > 25) val = val.substring(0, 25);
                    regInputs[key].value = val;
                }
                const value = regInputs[key].value.trim();
                validateField(key, value);
            });
        });

        const regFormElement = document.getElementById('register-form');
        if (regFormElement) {
            regFormElement.addEventListener('submit', async function(e) {
                e.preventDefault();

                let isFormValid = true;
                Object.keys(regInputs).forEach(key => {
                    const value = regInputs[key].value.trim();
                    if (!validateField(key, value)) isFormValid = false;
                });
                if (!isFormValid) return;

                const fullName = regInputs.fullname.value.trim();
                const email = regInputs.email.value.trim();
                const countryCode = document.getElementById('reg-country-code')?.value || '';
                const phone = countryCode + regInputs.phone.value;
                const username = regInputs.username.value.trim();
                const password = regInputs.password.value;

                regError.classList.remove('show');
                regSuccess.classList.remove('show');

                try {
                    // const reqBody = { fullName, email, phone, username, password };
                    const linkedin = regInputs.linkedin.value.trim();
                    const github = regInputs.github.value.trim();
                    const reqBody = { fullName, email, phone, username, password, linkedin, github };
                    const res = await fetch('/api/auth/signup', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(reqBody),
                        credentials: 'include'
                    });
                    const data = await res.json();
                    if (!res.ok) {
                        regError.textContent = '❌ ' + (data.error || 'Registration failed');
                        regError.classList.add('show');
                        return;
                    }
                    regSuccess.textContent = '✅ Registered successfully';
                    regSuccess.classList.add('show');
                    regFormElement.reset();
                    document.querySelectorAll('.input-group').forEach(group => group.classList.remove('valid', 'invalid'));
                    document.querySelectorAll('.field-error-msg').forEach(msg => msg.textContent = '');
                    setTimeout(() => {
                        const tabL = document.getElementById('tab-login');
                        if (tabL) tabL.click();
                        regSuccess.classList.remove('show');
                        window.location.href = 'login.html';
                    }, 1000);
                } catch (err) {
                    console.error(err);
                    regError.textContent = '❌ Connect Error';
                    regError.classList.add('show');
                }
            });
        }
    }

    // Clear Buttons
    const clearLoginBtn = document.getElementById('clear-login');
    const clearRegBtn = document.getElementById('clear-reg');
    
    if (clearLoginBtn) {
        clearLoginBtn.addEventListener('click', () => {
            if (loginForm) loginForm.reset();
            if (loginError) loginError.classList.remove('show');
        });
    }
    if (clearRegBtn) {
        clearRegBtn.addEventListener('click', () => {
            if (registerForm) registerForm.reset();
            if (regError) regError.classList.remove('show');
            const fileLabel = document.querySelector('.file-label');
            if (document.getElementById('reg-linkedin')) document.getElementById('reg-linkedin').value = '';
            if (document.getElementById('reg-github')) document.getElementById('reg-github').value = '';
            if (fileLabel) {
                fileLabel.textContent = 'Upload Profile Image';
                delete fileLabel.dataset.base64;
            }
        });
    }

    // Login submission
    const logFormElement = document.getElementById('login-form');
    if (logFormElement) {
        logFormElement.addEventListener('submit', async function(e) {
            e.preventDefault();
            const userOrEmail = document.getElementById('username').value.trim();
            const pass = document.getElementById('password').value;
            const logErr = document.getElementById('login-error');

            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: userOrEmail, password: pass }),
                    credentials: 'include'
                });
                const data = await res.json();
                if (res.ok) {
                    window.location.href = 'dashboard.html';
                } else {
                    if (logErr) {
                        logErr.textContent = '❌ ' + (data.error || 'Invalid credentials.');
                        logErr.classList.add('show');
                    }
                }
            } catch (err) {
                console.error(err);
                if (logErr) {
                    logErr.textContent = '❌ Connect Error';
                    logErr.classList.add('show');
                }
            }
        });
    }

    // Logout
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            try {
                await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
                window.location.replace('login.html?logout=true');
            } catch (err) {
                console.error(err);
                window.location.replace('login.html?logout=true');
            }
        });
    }

    // Clear inputs on login page load
    if (isLoginPage) {
        window.addEventListener('load', () => {
            document.querySelectorAll('input').forEach(inp => inp.value = '');
            if (loginForm) loginForm.reset();
            if (registerForm) registerForm.reset();
        });
    }

    // Profile and Settings Navigation
    const topProfileBtn = document.getElementById('topbar-profile-btn');
    const settingsBtn = document.getElementById('settings-btn');
    if (topProfileBtn) {
        topProfileBtn.style.cursor = 'pointer';
        topProfileBtn.addEventListener('click', () => {
            window.location.href = 'profile.html';
        });
    }
    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            window.location.href = 'profile.html';
        });
    }

    // Theme Toggle
    const themeBtn = document.getElementById('theme-switch');
    const currentTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);
    if (themeBtn) {
        themeBtn.innerHTML = currentTheme === 'dark' ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
        themeBtn.addEventListener('click', () => {
            const newTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            themeBtn.innerHTML = newTheme === 'dark' ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
        });
    }

    // Close icons on dashboard checklists
    const closeIcons = document.querySelectorAll('.close-icon');
    closeIcons.forEach(icon => {
        icon.addEventListener('click', function(e) {
            const parentItem = this.closest('.check-item');
            if(parentItem) parentItem.style.display = 'none';
        });
    });
});