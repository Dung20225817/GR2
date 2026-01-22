import TopMenu from "../UI_Components/TopMenu";
import { Link } from "react-router-dom";
import "../UI_Components/HomePage.css";
export default function HomePage() {
  const featureItems = [
    {
      img: "/image/feature1.jpg",
      title: "Feature 1",
      description: "Mô tả chức năng 1",
    },
    {
      img: "/image/feature2.jpg",
      title: "Feature 2",
      description: "Mô tả chức năng 2",
    },
    {
      img: "/image/feature3.jpg",
      title: "Feature 3",
      description: "Mô tả chức năng 3",
    },
    {
      img: "/image/feature4.jpg",
      title: "Feature 4",
      description: "Mô tả chức năng 4",
    },
  ];
  return (
    <div>
      <TopMenu />
      {/* nội dung trang */}
      <div className="images-container">
        <Link to="/multichoice" className="image-wrapper">
          <img src="/image/multichoice.jpg" alt="Multiple Choice" className="home-image" />
          <div className="image-text">Multiple Choice</div>
        </Link>
        <Link to="/handwritten" className="image-wrapper">
          <img src="/image/handwritten.jpg" alt="Handwritten Question" className="home-image" />
          <div className="image-text">Handwritten Question</div>
        </Link>
      </div>

      {/* 4 ô chữ nhật text */}
      <div className="features-container">
        {featureItems.map((item, index) => (
          <div className="feature-box" key={index}>
            <img src={item.img} alt={item.title} className="feature-img" />
            <h3>{item.title}</h3>
            <p>{item.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
