/**
 * Visualizador de PowerPoint propio
 * Maneja la navegación entre diapositivas y controles
 */

class PowerPointViewer {
    constructor(options = {}) {
        this.currentSlide = 1;
        this.totalSlides = options.totalSlides || 1;
        this.onSlideChange = options.onSlideChange || null;

        this.init();
    }

    init() {
        // Elementos del DOM
        this.prevBtn = document.getElementById('prev-slide');
        this.nextBtn = document.getElementById('next-slide');
        this.currentSlideSpan = document.getElementById('current-slide');
        this.totalSlidesSpan = document.getElementById('total-slides');
        this.thumbnails = document.querySelectorAll('.thumbnail');

        this.bindEvents();
        this.showSlide(1);
    }

    bindEvents() {
        // Event listeners para botones
        if (this.prevBtn) {
            this.prevBtn.addEventListener('click', () => this.previousSlide());
        }

        if (this.nextBtn) {
            this.nextBtn.addEventListener('click', () => this.nextSlide());
        }

        // Event listeners para miniaturas
        this.thumbnails.forEach(thumb => {
            thumb.addEventListener('click', () => {
                const slideNumber = parseInt(thumb.getAttribute('data-slide'));
                this.goToSlide(slideNumber);
            });
        });

        // Navegación con teclado
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                this.previousSlide();
            } else if (e.key === 'ArrowRight') {
                this.nextSlide();
            }
        });
    }

    showSlide(slideNumber) {
        // Ocultar todas las diapositivas
        document.querySelectorAll('.slide').forEach(slide => {
            slide.style.display = 'none';
        });

        // Mostrar la diapositiva actual
        const targetSlide = document.getElementById(`slide-${slideNumber}`);
        if (targetSlide) {
            targetSlide.style.display = 'block';
        }

        // Actualizar controles
        if (this.currentSlideSpan) {
            this.currentSlideSpan.textContent = slideNumber;
        }

        // Actualizar botones
        if (this.prevBtn) {
            this.prevBtn.disabled = slideNumber === 1;
        }
        if (this.nextBtn) {
            this.nextBtn.disabled = slideNumber === this.totalSlides;
        }

        // Actualizar miniaturas
        this.thumbnails.forEach(thumb => {
            thumb.classList.remove('active');
        });
        const activeThumb = document.querySelector(`.thumbnail[data-slide="${slideNumber}"]`);
        if (activeThumb) {
            activeThumb.classList.add('active');
        }

        this.currentSlide = slideNumber;

        // Callback
        if (this.onSlideChange) {
            this.onSlideChange(slideNumber);
        }
    }

    previousSlide() {
        if (this.currentSlide > 1) {
            this.showSlide(this.currentSlide - 1);
        }
    }

    nextSlide() {
        if (this.currentSlide < this.totalSlides) {
            this.showSlide(this.currentSlide + 1);
        }
    }

    goToSlide(slideNumber) {
        if (slideNumber >= 1 && slideNumber <= this.totalSlides) {
            this.showSlide(slideNumber);
        }
    }

    getCurrentSlide() {
        return this.currentSlide;
    }

    getTotalSlides() {
        return this.totalSlides;
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function () {
    const totalSlides = document.getElementById('total-slides');
    if (totalSlides) {
        const viewer = new PowerPointViewer({
            totalSlides: parseInt(totalSlides.textContent)
        });
    }
});
