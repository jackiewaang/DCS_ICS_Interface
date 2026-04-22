function NavItem({ icon, label, isActive, onClick, isCollapsed }) {
    return (
        <button onClick={onClick} title={isCollapsed ? label : ""}
        className={`w-full flex items-center transition-all duration-200 px-4 py-3 rounded-lg text-sm font-medium cursor-pointer ${
            isCollapsed ? "justify-center" : "gap-3"
        } ${
            isActive
            ? "bg-indigo-600 text-white shadow-md"
            : "hover:bg-slate-800 hover:text-white"
        }`}
        >
            {icon}
            {!isCollapsed && <span className="whitespace-nowrap overflow-hidden text-ellipsis">{label}</span>}
        </button>
    )
}

export default NavItem;