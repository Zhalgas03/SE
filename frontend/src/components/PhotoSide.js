import React, { useState, useEffect, useRef } from 'react';

const API_KEY = 'pmNK8CZbn2lOEr8vN8OERavIp3CsrUkmKqVcx9wAte03zTloVzTv5EHX'; // 🔁 Вставь свой ключ
const DEFAULT_IMAGE = './1.jpg'; // 🔁 Помести этот файл в public/

function PhotoSide() {
  const [photoUrl, setPhotoUrl] = useState(DEFAULT_IMAGE);
  const intervalRef = useRef(null);

  const loadPhoto = async () => {
    try {
      const page = Math.floor(Math.random() * 100) + 1;
      const url = `https://api.pexels.com/v1/search?query=travel&orientation=portrait&size=large&per_page=1&page=${page}`;

      const res = await fetch(url, {
        headers: {
          Authorization: API_KEY,
        },
      });

      const data = await res.json();
      const photo = data.photos?.[0];

      if (photo && photo.src?.large2x) {
        const img = new Image();
        img.src = photo.src.large2x;

        img.onload = () => {
          setPhotoUrl(photo.src.large2x);
          console.log('✅ New photo loaded:', photo.src.large2x);

          if (!intervalRef.current) {
            intervalRef.current = setInterval(() => {
              loadPhoto();
            }, 60000);
          }
        };
      } else {
        console.log('⛔ No valid photo, trying again...');
        loadPhoto();
      }
    } catch (err) {
      console.error('❌ Ошибка при загрузке фото:', err);
    }
  };

  useEffect(() => {
    const preload = setTimeout(() => {
      loadPhoto();
    }, 200);

    return () => {
      clearTimeout(preload);
      clearInterval(intervalRef.current);
    };
  }, []);

  return (
    <div
      className="col-md-6"
      style={{
        backgroundImage: `url(${photoUrl})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        height: '100vh',
        transition: 'background-image 1s ease-in-out',
      }}
    />
  );
}

export default PhotoSide;
