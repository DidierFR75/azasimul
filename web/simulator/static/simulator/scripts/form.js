
window.onload = () => {
    [...document.getElementsByClassName('field-wrp') ].forEach(wrapper => {
        const input = [...wrapper.children].find(item => ['INPUT', 'TEXTAREA', 'SELECT'].includes(item.tagName))
        if(input.value.length) wrapper.dataset.focus = true
        input.addEventListener('focus', () => {
            wrapper.dataset.focus = true
        })
        input.addEventListener('blur', () => {
            if(!input.value.length) wrapper.dataset.focus = false
        })
    })
}