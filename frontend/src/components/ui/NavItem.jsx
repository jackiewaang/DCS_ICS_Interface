function NavItem({ icon, label, isActive, onClick, isCollapsed }) {
    return (
        <button onClick={onClick} title={isCollapsed ? label : ""}
        className={`w-full flex items-center transition-all duration-200 px-3 py-2.5 rounded-md text-sm font-medium cursor-pointer ${
            isCollapsed ? "justify-center" : "gap-3"
        } ${
            isActive
            ? "bg-slate-100 text-slate-900 shadow-sm"
            : "hover:bg-slate-100 hover:text-slate-900"
        }`}
        >
            {icon}
            {!isCollapsed && <span className="whitespace-nowrap overflow-hidden text-ellipsis">{label}</span>}
        </button>
    )
}

export default NavItem;