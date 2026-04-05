// File: frontend/src/context/FirebaseAuthContext.jsx

import React, { createContext, useState, useContext, useEffect } from 'react';
import { 
  getCurrentUser, 
  loginUser, 
  registerUser, 
  logoutUser 
} from '../services/firebaseService';
import { localLogin, localRegister } from '../services/api';

const FirebaseAuthContext = createContext(null);

export const useFirebaseAuth = () => {
  const context = useContext(FirebaseAuthContext);
  if (!context) {
    throw new Error('useFirebaseAuth must be used within FirebaseAuthProvider');
  }
  return context;
};

export const FirebaseAuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [authMode, setAuthMode] = useState('firebase'); // 'firebase' or 'local'

  useEffect(() => {
    checkUser();
  }, []);

  const checkUser = async () => {
    try {
      const currentUser = await getCurrentUser();
      if (currentUser) {
        const token = await currentUser.getIdToken();
        localStorage.setItem('access_token', token);
        setUser({
          uid: currentUser.uid,
          email: currentUser.email,
          username: currentUser.displayName || currentUser.email.split('@')[0],
          isLocal: false
        });
        setAuthMode('firebase');
      } else {
        // Check if local token exists
        const localToken = localStorage.getItem('access_token');
        if (localToken) {
          // If we have a token but firebase is not active, treat as potential local user
          setUser({ email: 'local-user', isLocal: true });
          setAuthMode('local');
        }
      }
    } catch (err) {
      console.error("Auth check error:", err);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    setError(null);
    
    // 1. Try Firebase First
    const firebaseResult = await loginUser(email, password);
    
    if (firebaseResult.success) {
      const token = await firebaseResult.user.getIdToken();
      localStorage.setItem('access_token', token);
      setUser(firebaseResult.user);
      setAuthMode('firebase');
      return { success: true };
    } 
    
    // 2. Firebase failed — always try local backend auth as fallback
    console.warn("Firebase login failed. Trying local backend auth...");
    try {
      const localResult = await localLogin(email, password);
      if (localResult.success) {
        setUser({ email, isLocal: true });
        setAuthMode('local');
        return { success: true };
      }
    } catch (localErr) {
      console.error("Local login also failed:", localErr);
    }
    
    // 3. Both failed
    const errorMsg = "Login failed. Please check your credentials.";
    setError(errorMsg);
    return { success: false, error: errorMsg };
  };

  const register = async (email, password, userData) => {
    setError(null);
    
    // 1. Try Firebase First
    const firebaseResult = await registerUser(email, password, userData);
    
    if (firebaseResult.success) {
      const token = await firebaseResult.user.getIdToken();
      localStorage.setItem('access_token', token);
      setUser(firebaseResult.user);
      setAuthMode('firebase');
      return { success: true };
    }
    
    // 2. Fallback to Local
    if (firebaseResult.error?.includes('configuration-not-found')) {
      const localResult = await localRegister(email, password, userData.username, userData.skillLevel);
      if (localResult.success) {
        // Automatically login after register locally
        await localLogin(email, password);
        setUser({ email, isLocal: true });
        setAuthMode('local');
        return { success: true };
      }
    }
    
    setError(firebaseResult.error);
    return { success: false, error: firebaseResult.error };
  };

  const logout = async () => {
    if (authMode === 'firebase') {
      await logoutUser();
    }
    localStorage.removeItem('access_token');
    setUser(null);
    return { success: true };
  };

  return (
    <FirebaseAuthContext.Provider value={{
      user,
      loading,
      error,
      login,
      register,
      logout,
      isAuthenticated: !!user,
      authMode
    }}>
      {children}
    </FirebaseAuthContext.Provider>
  );
};
