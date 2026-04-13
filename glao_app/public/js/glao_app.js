// from: developer.mozilla.org/en-US/docs/Web/API/Window/beforeunload_event
window.addEventListener("beforeunload", (e) => {
    if (cur_frm && cur_frm.doc && cur_frm.doc.__unsaved) {
        e.preventDefault();
    }
});
