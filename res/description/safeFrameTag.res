CONTAINER Tsafeframetag
{
    NAME Tsafeframetag;
    INCLUDE Tbase;
    
    GROUP ID_TAGPROPERTIES
    {
        LONG BACKGROUND_VISIBILITY
        {
            CYCLE
            {
                Tsafeframetag::VIEW_THROUGH_CAMERA;
                Tsafeframetag::ALWAYS;
                Tsafeframetag::NEVER;
                Tsafeframetag::ONLY_NOT_THROUGH_CAM;
            }
        }

        LONG SAFE_FRAME_VISIBILITY
        {
            CYCLE
            {
                Tsafeframetag::VIEW_THROUGH_CAMERA;
                Tsafeframetag::ALWAYS;
                Tsafeframetag::NEVER;
                Tsafeframetag::ONLY_NOT_THROUGH_CAM;
            }
        }
        
        LONG VIEWPORT_GRID_VISIBILITY
        {
            CYCLE
            {
                Tsafeframetag::VIEW_THROUGH_CAMERA;
                Tsafeframetag::ALWAYS;
                Tsafeframetag::NEVER;
                Tsafeframetag::ONLY_NOT_THROUGH_CAM;
            }
        }
    }
}
