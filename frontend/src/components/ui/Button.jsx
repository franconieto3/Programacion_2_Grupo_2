import "./Button.css";

const Button = ({ 
  children, 
  variant = "default", 
  size = "default", 
  className = "", 
  ...props 
}) => {
  
  // Construimos la cadena de clases CSS basándonos en las props
  const baseClass = "btn-base";
  const variantClass = `btn-variant-${variant}`;
  const sizeClass = `btn-size-${size}`;

  // Combinamos las clases, permitiendo además clases extra mediante la prop className
  const combinedClasses = `${baseClass} ${variantClass} ${sizeClass} ${className}`.trim();

  return (
    <button className={combinedClasses} {...props}>
      {children}
    </button>
  );
};

export default Button;