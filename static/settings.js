// Generative AI Sales Agent - Settings & FAQs JS Engine

document.addEventListener('DOMContentLoaded', () => {
  const triggers = document.querySelectorAll('.faq-trigger');
  
  triggers.forEach(trigger => {
    trigger.addEventListener('click', () => {
      const panel = trigger.nextElementSibling;
      const icon = trigger.querySelector('i');
      
      // Accordion toggle: Collapse other active panels first
      document.querySelectorAll('.faq-panel').forEach(p => {
        if (p !== panel && p.style.maxHeight) {
          p.style.maxHeight = null;
          p.parentElement.classList.remove('open');
          const otherIcon = p.previousElementSibling.querySelector('i');
          if (otherIcon) otherIcon.style.transform = 'rotate(0deg)';
        }
      });
      
      // Toggle the selected panel
      if (panel.style.maxHeight) {
        panel.style.maxHeight = null;
        trigger.parentElement.classList.remove('open');
        if (icon) icon.style.transform = 'rotate(0deg)';
      } else {
        panel.style.maxHeight = panel.scrollHeight + "px";
        trigger.parentElement.classList.add('open');
        if (icon) icon.style.transform = 'rotate(180deg)';
      }
    });
  });
});
