# E-05 T-05 — Theming completo (tokens E-02) y diseño responsive
# Tipo: Código, sin TDD — rama + PR propia, validación manual (D-030, mismo
# patrón que E06-T07 y E05-T04). Alcance ampliado por D-038: el theming de
# E-02 no se aplicaba al Chainlit real (variables/clases .cl-* inexistentes);
# esta tarea crea design/public/theme.json y corrige selectores de style.css
# sobre clases reales del DOM, identificadas en Antigravity con devtools.
#
# Referencia visual (no de selectores DOM — son comps estáticos, ver D-038):
# docs/design/screens/AIIP Phase 2 - Chat.dc.html es la referencia principal
# para esta tarea (layout del chat, dark/light, family/professional).
# docs/design/screens/AIIP Identity - Phase 1.dc.html sirve de referencia
# adicional de tipografía/paleta base. AIIP Phase 2 - Auth.dc.html no aplica
# a esta tarea (fuera de alcance, ver T-06).

Feature: Theming completo y diseño responsive del chat familiar

  Como familiar en móvil o escritorio
  Quiero que la interfaz use la identidad visual de AIIP y funcione en cualquier dispositivo
  Para tener una experiencia de producto coherente y usable

  # Checklist de verificación manual
  # Marca cada punto al ejecutar la tarea

  Scenario: El mecanismo de theming se carga correctamente
    Given abro la app familiar con design/public/theme.json y el style.css corregido desplegados
    When inspecciono la app con las devtools del navegador
    Then las variables reales de Chainlit (--primary, --background, --foreground, --accent, --border, --sidebar-*, --radius) reflejan los valores de design/public/tokens.css, no los valores por defecto de Chainlit

  Scenario: Theming en escritorio coincide con los tokens de E-02
    Given abro la app familiar en escritorio
    When cargo el chat
    Then los colores, tipografía y estilo del input coinciden con design/public/tokens.css y style.css
    And el resultado visual es consistente con "docs/design/screens/AIIP Phase 2 - Chat.dc.html" (referencia de diseño, variante Family · Dark)

  Scenario: Interfaz usable en viewport móvil
    Given abro la app familiar en un viewport móvil, por ejemplo 375px de ancho
    When interactúo con el chat: escribir, enviar, hacer scroll
    Then no hay scroll horizontal ni elementos cortados o solapados

  Scenario: Los pasos intermedios del RAG también respetan el theming
    Given una respuesta que muestra el paso "Documentos consultados" de T-03
    When reviso su estilo visual
    Then es coherente con el resto del theming de la app, no un componente sin estilizar
