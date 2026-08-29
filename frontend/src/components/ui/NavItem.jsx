function NavItem({ icon, label, isActive, onClick, isCollapsed }) {
    return (
        <button onClick={onClick} title={isCollapsed ? label : ""}
        className={`w-full flex items-center transition-all duration-200 px-3 py-2.5 rounded-md text-sm font-medium cursor-pointer ${
            isCollapsed ? "justify-center" : "gap-3"
        } ${
            isActive
            ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm"
            : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
        }`}
        >
            {icon}
            {!isCollapsed && <span className="whitespace-nowrap overflow-hidden text-ellipsis">{label}</span>}
        </button>
    )
}

export default NavItem;
