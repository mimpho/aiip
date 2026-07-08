# E-05 T-05 — Theming completo (tokens E-02) y diseño responsive
# Tipo: Configuración manual — verificación sin tests automatizados (D-030)

Feature: Theming completo y diseño responsive del chat familiar

  Como familiar en móvil o escritorio
  Quiero que la interfaz use la identidad visual de AIIP y funcione en cualquier dispositivo
  Para tener una experiencia de producto coherente y usable

  # Checklist de verificación manual
  # Marca cada punto al ejecutar la tarea

  Scenario: Theming en escritorio coincide con los tokens de E-02
    Given abro la app familiar en escritorio
    When cargo el chat
    Then los colores, tipografía y estilo del input coinciden con design/public/tokens.css y style.css

  Scenario: Interfaz usable en viewport móvil
    Given abro la app familiar en un viewport móvil, por ejemplo 375px de ancho
    When interactúo con el chat: escribir, enviar, hacer scroll
    Then no hay scroll horizontal ni elementos cortados o solapados

  Scenario: Los pasos intermedios del RAG también respetan el theming
    Given una respuesta que muestra el paso "Consultando fuentes" de T-03
    When reviso su estilo visual
    Then es coherente con el resto del theming de la app, no un componente sin estilizar
