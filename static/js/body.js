function autocomplete(input, arr) {
    input.on("input", function (e) {
        inputText = this.value;
        var displayed = []
        arr.forEach(a => {
            var group = $("#" + a)
            if (a.toLowerCase().includes(inputText.toLowerCase())) {
                group.css("display", "block");
                displayed.push(group)
            } else {
                group.css("display", "none");
                group.css("animation", 'none');
            }
        })
        displayed.forEach(e => {
            var z = $(e).offset().top, o = $(window).height(), a = $(window).scrollTop()
            if (z - 0.8 * o <= a && a < z) {
                window.matchMedia("(max-width: 800px)").matches ? w = '0s' : w = $(e).attr("animation-delay");
                $(e).css("animation", $(e).attr("animation-style") + " " + $(e).attr("animation-duration") + " forwards " + w + " ease-in-out");
            }
        })
    })
}