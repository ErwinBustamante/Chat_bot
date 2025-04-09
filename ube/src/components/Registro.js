import React, { useState } from 'react';
import "../css/Registro.css";

const Registro = ({ onClose }) => {
  const [formData, setFormData] = useState({
    nombre: '',
    cedula: '',
    correo: '',
    celular: '',
    carrera: ''
  });

  const [errors, setErrors] = useState({
    nombre: '',
    cedula: '',
    correo: '',
    celular: '',
    carrera: ''
  });

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const carreras = [
    "Derecho",
    "Ingeniería Eléctrica",
    "Ingeniería en Sistemas Inteligentes",
    "Ingeniería en Biomedicina",
    "Licenciatura en Administración de Empresas",
    "Licenciatura en Auditoría y Control de Gestión",
    "Licenciatura en Ciencias de la Educación",
    "Licenciatura en Contabilidad y Finanzas",
    "Licenciatura en Enfermería",
    "Licenciatura en Fisioterapia",
    "Licenciatura en Psicología",
    "Licenciatura en Seguridad y Salud Ocupacional",
    "Odontología"
  ];

  const validateEmail = (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  };

  const validateCedula = (cedula) => {

    return /^\d{10}$/.test(cedula);
  };

  const validateCelular = (celular) => {
    
    return /^(09\d{8}|\+593\d{9})$/.test(celular);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    

    if (name === 'correo' && value && !validateEmail(value)) {
      setErrors(prev => ({ ...prev, correo: 'Correo electrónico no válido' }));
    } else if (name === 'cedula' && value && !validateCedula(value)) {
      setErrors(prev => ({ ...prev, cedula: 'Cédula debe tener 10 dígitos' }));
    } else if (name === 'celular' && value && !validateCelular(value)) {
      setErrors(prev => ({ ...prev, celular: 'Celular no válido (ej: 0987654321 o +593987654321)' }));
    } else {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    let valid = true;
    const newErrors = { ...errors };

    if (!formData.nombre.trim()) {
      newErrors.nombre = 'Nombre completo es requerido';
      valid = false;
    }

    if (!formData.cedula) {
      newErrors.cedula = 'Cédula es requerida';
      valid = false;
    } else if (!validateCedula(formData.cedula)) {
      newErrors.cedula = 'Cédula debe tener 10 dígitos';
      valid = false;
    }

    if (!formData.correo) {
      newErrors.correo = 'Correo electrónico es requerido';
      valid = false;
    } else if (!validateEmail(formData.correo)) {
      newErrors.correo = 'Correo electrónico no válido';
      valid = false;
    }

    if (!formData.celular) {
      newErrors.celular = 'Celular es requerido';
      valid = false;
    } else if (!validateCelular(formData.celular)) {
      newErrors.celular = 'Celular no válido (ej: 0987654321 o +593987654321)';
      valid = false;
    }

    if (!formData.carrera) {
      newErrors.carrera = 'Debe seleccionar una carrera';
      valid = false;
    }

    setErrors(newErrors);
    return valid;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:5000/pre-registro', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Error en el registro');
      }

      setSuccess(true);
      setTimeout(() => {
        onClose();
      }, 3000); 
      
    } catch (error) {
      console.error('Error:', error);
      setError(error.message || 'Error al registrar, por favor intente nuevamente');
    } finally {
      setLoading(false);
    }
  };


  if (loading) {
    return (
      <div className="registro-modal">
        <div className="registro-contenido">
          <div className="registro-cargando">
            <div className="registro-spinner"></div>
            <p>Enviando tus datos...</p>
          </div>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="registro-modal">
        <div className="registro-contenido">
          <button onClick={onClose} className="registro-cerrar">
            &times;
          </button>
          <div className="registro-exito">
            <svg viewBox="0 0 24 24" className="registro-icono-exito">
              <path fill="currentColor" d="M12 2C6.5 2 2 6.5 2 12S6.5 22 12 22 22 17.5 22 12 17.5 2 12 2M10 17L5 12L6.41 10.59L10 14.17L17.59 6.58L19 8L10 17Z" />
            </svg>
            <h3>¡Registro Exitoso!</h3>
            <p>Tu información ha sido enviada correctamente.</p>
            <p>Un asesor se pondrá en contacto contigo pronto.</p>
            <button 
              onClick={onClose} 
              className="registro-boton"
              style={{ marginTop: '20px' }}
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="registro-modal">
      <div className="registro-contenido">
        <button onClick={onClose} className="registro-cerrar">
          &times;
        </button>
        <h2 className="registro-titulo">Formulario de Registro</h2>
        
        {error && (
          <div className="registro-error">
            <p>{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="registro-formulario">
          <div className="registro-grupo">
            <label className="registro-etiqueta">Nombre Completo:</label>
            <input
              type="text"
              name="nombre"
              className="registro-input"
              value={formData.nombre}
              onChange={handleChange}
              required
            />
            {errors.nombre && <span className="registro-mensaje-error">{errors.nombre}</span>}
          </div>

          <div className="registro-grupo">
            <label className="registro-etiqueta">Cédula:</label>
            <input
              type="text"
              name="cedula"
              className="registro-input"
              value={formData.cedula}
              onChange={handleChange}
              required
              maxLength="10"
              placeholder="Ej: 1234567890"
            />
            {errors.cedula && <span className="registro-mensaje-error">{errors.cedula}</span>}
          </div>

          <div className="registro-grupo">
            <label className="registro-etiqueta">Correo Electrónico:</label>
            <input
              type="email"
              name="correo"
              className="registro-input"
              value={formData.correo}
              onChange={handleChange}
              required
              placeholder="Ej: usuario@dominio.com"
            />
            {errors.correo && <span className="registro-mensaje-error">{errors.correo}</span>}
          </div>

          <div className="registro-grupo">
            <label className="registro-etiqueta">Celular:</label>
            <input
              type="tel"
              name="celular"
              className="registro-input"
              value={formData.celular}
              onChange={handleChange}
              required
              placeholder="Ej: 0987654321 o +593987654321"
            />
            {errors.celular && <span className="registro-mensaje-error">{errors.celular}</span>}
          </div>

          <div className="registro-grupo">
            <label className="registro-etiqueta">Carrera:</label>
            <select
              name="carrera"
              className="registro-select"
              value={formData.carrera}
              onChange={handleChange}
              required
            >
              <option value="">Seleccione una carrera</option>
              {carreras.map((carrera, index) => (
                <option key={index} value={carrera} className="registro-opcion">
                  {carrera}
                </option>
              ))}
            </select>
            {errors.carrera && <span className="registro-mensaje-error">{errors.carrera}</span>}
          </div>

          <button 
            type="submit" 
            className="registro-boton"
            disabled={loading}
          >
            {loading ? 'Enviando...' : 'Enviar Registro'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Registro;