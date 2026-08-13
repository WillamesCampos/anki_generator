// Tokens de design extraídos de refs/Ashley_files/style.css — ver AUDIT.md
// para a fonte de cada valor. Nenhum valor aqui deve ser editado sem
// atualizar a auditoria correspondente.

export const colors = {
  accent: "rgb(255, 152, 0)",
  textPrimary: "rgb(0, 0, 0)",
  textSecondary: "rgba(0, 0, 0, 0.5)",
  textOnDark: "rgba(255, 255, 255, 0.9)",
  border: "rgba(0, 0, 0, 0.1)",
  bgLight: "rgb(242, 242, 242)",
  bgDark: "rgb(0, 0, 0)",
  white: "rgb(255, 255, 255)",
};

export const typography = {
  fontFamily: '"Outfit", sans-serif',
  fontSizeBase: "16px",
  lineHeightBase: "150%",
  // Escala adaptada da cascata de headlines do template (86px -> 34px),
  // proporcionalmente reduzida para contexto de dashboard — ver AUDIT.md.
  fontSizeXl: "32px",
  fontSizeLg: "22px",
  fontSizeMd: "18px",
  fontSizeSm: "14px",
};

export const spacing = {
  xs: "10px",
  sm: "15px",
  md: "30px",
  lg: "50px",
  xl: "60px",
};

export const radius = {
  pill: "70px",
  card: "16px", // adaptado de 40px — ver nota em AUDIT.md
  circle: "50%",
};
