document.addEventListener("DOMContentLoaded", function () {
    particlesJS("particles-js", {
        "particles": {
            "number": {
                "value": window.innerWidth < 768 ? 60 : 100,
                "density": {
                    "enable": true,
                    "value_area": 800
                }
            },
            "color": {
                "value": "#00FFFF"
            },
            "shape": {
                "type": "circle"
            },
            "opacity": {
                "value": 0.7,
                "random": true,
                "anim": {
                    "enable": true,
                    "speed": 0.5
                }
            },
            "size": {
                "value": 3,
                "random": true,
                "anim": {
                    "enable": true,
                    "speed": 1
                }
            },
            "line_linked": {
                "enable": true,
                "distance": 150,
                "color": "#00FFFF",
                "opacity": 0.6,
                "width": 1
            },
            "move": {
                "enable": true,
                "speed": 2,
                "direction": "none",
                "random": false,
                "straight": false,
                "out_mode": "out",
                "bounce": false
            }
        }
    });
  
    window.addEventListener("resize", function () {
        particlesJS("particles-js", {
            "particles": {
                "number": {
                    "value": window.innerWidth < 768 ? 60 : 100
                }
            }
        });
    });
  });
  
  // Show login form after logo animation (~3.3s delay)
  window.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
      document.getElementById('loginBox').classList.add('show');
    }, 2300); // or match your logo animation duration
  });
  // Select the neon button
const neonButton = document.querySelector('.neon-btn');

// Add event listener for click
neonButton.addEventListener('click', function() {
  this.classList.add('active');
});
window.addEventListener('load', function () {
    particlesJS.load('particles-js', 'particles.json', function () {
        console.log('Particles.js config loaded');
    });
});