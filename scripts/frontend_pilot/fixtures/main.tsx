import React from 'react';
import {createRoot} from 'react-dom/client';
import Fixture from 'fixture-component';
import 'fixture-css';
document.body.style.padding='100px';
createRoot(document.getElementById('root')!).render(<Fixture/>);
