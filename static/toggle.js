window.addEventListener('load', () => {
    // console.log("setting toggles");
    document.querySelectorAll('[data-toggle]').forEach((item) => {
        // console.log(item.dataset.toggle);
        var that = document.getElementById(item.dataset.toggle);
        if (that) {
            // console.log(that);
            item.addEventListener('click', (e) => {
                // console.log("Toggle", item.dataset.toggle);
                if (!e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                    that.checked = !that.checked;
                }
            });
        } else {
            console.warn("Could not find toggled element", item.dataset.toggle)
        }
    });
});
