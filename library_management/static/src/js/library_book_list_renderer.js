/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { ListController } from "@web/views/list/list_controller";
import { Component, onMounted, onPatched, onWillUnmount, useState, xml } from "@odoo/owl";

// Tooltip Component
class DescriptionTooltip extends Component {
    /** Tooltip for book descriptions
     * Displays a tooltip with the book's description when hovering over the book item.
     * The tooltip is positioned near the mouse cursor.
     * * This component is designed to be used within the LibraryBookListRenderer.
     * * It uses the `useState` hook to manage its visibility and position.
     * * The API provides methods to show the tooltip at a specific position and hide it.
     * * The tooltip is styled to be fixed in position and has a maximum width.
     */
    static template = xml`
        <div class="book-tooltip p-2 bg-light border shadow-sm"
             t-att-style="state.style">
            <t t-esc="state.description"/>
        </div>
    `;
    
    setup() {
        this.state = useState({ 
            style: "display: none;",
            description: "" 
        });
        
        // Expose API to parent component
        this.props.registerAPI({
            showAt: (x, y, description) => this.showAt(x, y, description),
            hide: () => this.hide()
        });
    }

    showAt(x, y, description) {
    const tooltipWidth = 300;
    if (x + tooltipWidth > window.innerWidth) {
    x = window.innerWidth - tooltipWidth - 10;
    }
    this.state.description = description;
    this.state.style = `
        display: block; 
        position: fixed; 
        top: ${y}px; 
        left: ${x}px; 
        z-index: 9999; 
        pointer-events: none;
        max-width: 300px;
    `;

 

    }

    hide() {
        this.state.style = "display: none;";
    }
}

// Custom Renderer
class LibraryBookListRenderer extends ListRenderer {
    /** Custom List Renderer for Library Book List
     * This renderer extends the default ListRenderer to add a tooltip feature
     * that displays the book's description when hovering over a book item.
     * It sets up event listeners for mouseover and mouseout events to show and hide
     * the tooltip.
     * * The tooltip is positioned dynamically based on the mouse cursor position
     *   and the dimensions of the book item.
     * * The tooltip is styled to be fixed in position and has a maximum width.
     * * The API provides methods to show the tooltip at a specific position and hide it.
     * * The renderer uses the `DescriptionTooltip` component to manage the tooltip's
     *   visibility and content.
     */
    static template = xml`
        <div>
            <t t-call="web.ListRenderer"/>
            <DescriptionTooltip 
                t-if="state.tooltipMounted"
                registerAPI="registerTooltipAPI"
            />
        </div>
    `;
    
    static components = { 
        ...ListRenderer.components,
        DescriptionTooltip 
    };

    setup() {
        super.setup();
        this.tooltipAPI = null;
        this.state = useState({ tooltipMounted: false });
        
        onMounted(() => {
            this.state.tooltipMounted = true;
            this.setupEventDelegation();
        });
        
        onPatched(() => this.setupEventDelegation());
        onWillUnmount(() => this.cleanup());
    }

    registerTooltipAPI = (api) => {
        this.tooltipAPI = api;
    };

    setupEventDelegation() {
        const table = this.tableRef?.el;
        if (!table) return;
        
        // Clean up previous listeners
        table.removeEventListener('mouseover', this.onMouseOver);
        table.removeEventListener('mouseout', this.onMouseOut);
        
        // Create new bound handlers
        this.onMouseOver = this.handleMouseOver.bind(this);
        this.onMouseOut = this.handleMouseOut.bind(this);
        
        // Add new listeners
        table.addEventListener('mouseover', this.onMouseOver);
        table.addEventListener('mouseout', this.onMouseOut);
    }

    handleMouseOver(event) {
    if (!this.tooltipAPI) return;

    const row = event.target.closest('tr[data-id]');
    if (!row) return;

    const id = row.getAttribute('data-id');
    const record = this.props.list.records.find(r => r.id.toString() === id);
    const description = record?.data?.description;
    if (!description) return;

    const rect = row.getBoundingClientRect();
    const scrollY = window.scrollY || window.pageYOffset;
    const scrollX = window.scrollX || window.pageXOffset;

    const tooltipWidth = 300;
    const tooltipHeight = 80;

    let left = rect.left + scrollX;
    let top = rect.bottom + scrollY + 5;

    if (left + tooltipWidth > window.innerWidth + scrollX) {
        left = window.innerWidth + scrollX - tooltipWidth - 10;
    }


    if (top + tooltipHeight > window.innerHeight + scrollY) {
        top = rect.top + scrollY - tooltipHeight - 5;
    }

 
    left = Math.max(left, scrollX + 10);
    top = Math.max(top, scrollY + 10);

    this.tooltipAPI.showAt(left, top, description);
}

    handleMouseOut(event) {
        if (!this.tooltipAPI) return;
        
        const row = event.target.closest('tr[data-id]');
        if (row) {
            this.tooltipAPI.hide();
        }
    }

    cleanup() {
        const table = this.tableRef?.el;
        if (table) {
            table.removeEventListener('mouseover', this.onMouseOver);
            table.removeEventListener('mouseout', this.onMouseOut);
        }
        this.tooltipAPI = null;
    }
}

// Controller
class LibraryBookListController extends ListController {}

// View Definition
const LibraryBookListView = {
    ...listView,
    Renderer: LibraryBookListRenderer,
    Controller: LibraryBookListController,
    fields: ["name", "description"],
};

registry.category("views").add("library_book_list", LibraryBookListView);