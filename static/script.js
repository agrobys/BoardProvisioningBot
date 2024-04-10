const elements = document.querySelectorAll('.movable-element');

elements.forEach(element => {
    element.addEventListener('mousedown', startDragging);
});

function startDragging(e) {
    const initialX = e.clientX + window.scrollX;
    const initialY = e.clientY + window.scrollY;
    const rect = e.target.getBoundingClientRect();
    const offsetX = initialX - rect.left;
    const offsetY = initialY - rect.top;

    document.addEventListener('mousemove', moveElement);
    document.addEventListener('mouseup', stopDragging);

    function moveElement(e) {
        const newX = e.clientX + window.scrollX - offsetX;
        const newY = e.clientY + window.scrollY - offsetY;

        // Ensure the element doesn't move beyond the viewport boundaries
        const maxX = window.innerWidth - rect.width;
        const maxY = window.innerHeight - rect.height;
        const constrainedX = Math.max(0, Math.min(newX, maxX));
        const constrainedY = Math.max(0, Math.min(newY, maxY));

        e.target.style.left = `${constrainedX}px`;
        e.target.style.top = `${constrainedY}px`;
    }

    function stopDragging() {
        document.removeEventListener('mousemove', moveElement);
        document.removeEventListener('mouseup', stopDragging);
    }
}