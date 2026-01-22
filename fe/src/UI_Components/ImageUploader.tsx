export default function ImageUploader({ onClick }: { onClick: () => void }) {
    return (
        <div className="upload-box" onClick={onClick}>
            <span className="plus">+</span>
        </div>
    );
}
