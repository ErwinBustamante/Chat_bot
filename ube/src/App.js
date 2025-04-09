import React from "react";
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Chat from "./components/Chat_bot";
import Registro from './components/Registro';


function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={
            <>
              
              <Chat />
            </>
          } />
          <Route path="/registro" element={<Registro />} />
          
        
        </Routes>
      </div>
    </Router>
  );
}

export default App;